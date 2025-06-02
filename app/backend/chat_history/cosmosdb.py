import os
import time
from datetime import timedelta
from typing import Any, Union

from azure.cosmos.aio import ContainerProxy, CosmosClient
from azure.identity.aio import AzureDeveloperCliCredential, ManagedIdentityCredential
from quart import Blueprint, current_app, jsonify, make_response, request
from quart_rate_limiter import rate_limit

from config import (
    CONFIG_CHAT_HISTORY_COSMOS_ENABLED,
    CONFIG_COSMOS_HISTORY_CLIENT,
    CONFIG_COSMOS_HISTORY_CONTAINER,
    CONFIG_COSMOS_FEEDBACK_CONTAINER,
    CONFIG_COSMOS_HISTORY_VERSION,
    CONFIG_CREDENTIAL,
)
from decorators import authenticated
from error import error_response

chat_history_cosmosdb_bp = Blueprint("chat_history_cosmos", __name__, static_folder="static")


@chat_history_cosmosdb_bp.post("/chat_history")
@authenticated
async def post_chat_history(auth_claims: dict[str, Any]):
    if not current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED]:
        return jsonify({"error": "Chat history not enabled"}), 400

    container: ContainerProxy = current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER]
    if not container:
        return jsonify({"error": "Chat history not enabled"}), 400

    entra_oid = auth_claims.get("oid")
    if not entra_oid:
        return jsonify({"error": "User OID not found"}), 401

    try:
        request_json = await request.get_json()
        session_id = request_json.get("id")
        message_pairs = request_json.get("answers")
        first_question = message_pairs[0][0]
        title = first_question + "..." if len(first_question) > 50 else first_question
        timestamp = int(time.time() * 1000)

        # Insert the session item:
        session_item = {
            "id": session_id,
            "version": current_app.config[CONFIG_COSMOS_HISTORY_VERSION],
            "session_id": session_id,
            "entra_oid": entra_oid,
            "type": "session",
            "title": title,
            "timestamp": timestamp,
        }

        message_pair_items = []
        # Now insert a message item for each question/response pair:
        for ind, message_pair in enumerate(message_pairs):
            message_pair_items.append(
                {
                    "id": f"{session_id}-{ind}",
                    "version": current_app.config[CONFIG_COSMOS_HISTORY_VERSION],
                    "session_id": session_id,
                    "entra_oid": entra_oid,
                    "type": "message_pair",
                    "question": message_pair[0],
                    "response": message_pair[1],
                }
            )

        batch_operations = [("upsert", (session_item,))] + [
            ("upsert", (message_pair_item,)) for message_pair_item in message_pair_items
        ]
        await container.execute_item_batch(batch_operations=batch_operations, partition_key=[entra_oid, session_id])
        return jsonify({}), 201
    except Exception as error:
        return error_response(error, "/chat_history")


@chat_history_cosmosdb_bp.get("/chat_history/sessions")
@authenticated
async def get_chat_history_sessions(auth_claims: dict[str, Any]):
    if not current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED]:
        return jsonify({"error": "Chat history not enabled"}), 400

    container: ContainerProxy = current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER]
    if not container:
        return jsonify({"error": "Chat history not enabled"}), 400

    entra_oid = auth_claims.get("oid")
    if not entra_oid:
        return jsonify({"error": "User OID not found"}), 401

    try:
        count = int(request.args.get("count", 10))
        continuation_token = request.args.get("continuation_token")

        res = container.query_items(
            query="SELECT c.id, c.entra_oid, c.title, c.timestamp FROM c WHERE c.entra_oid = @entra_oid AND c.type = @type ORDER BY c.timestamp DESC",
            parameters=[dict(name="@entra_oid", value=entra_oid), dict(name="@type", value="session")],
            partition_key=[entra_oid],
            max_item_count=count,
        )

        pager = res.by_page(continuation_token)

        # Get the first page, and the continuation token
        sessions = []
        try:
            page = await pager.__anext__()
            continuation_token = pager.continuation_token  # type: ignore

            async for item in page:
                sessions.append(
                    {
                        "id": item.get("id"),
                        "entra_oid": item.get("entra_oid"),
                        "title": item.get("title", "untitled"),
                        "timestamp": item.get("timestamp"),
                    }
                )

        # If there are no more pages, StopAsyncIteration is raised
        except StopAsyncIteration:
            continuation_token = None

        return jsonify({"sessions": sessions, "continuation_token": continuation_token}), 200

    except Exception as error:
        return error_response(error, "/chat_history/sessions")


@chat_history_cosmosdb_bp.get("/chat_history/sessions/<session_id>")
@authenticated
async def get_chat_history_session(auth_claims: dict[str, Any], session_id: str):
    if not current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED]:
        return jsonify({"error": "Chat history not enabled"}), 400

    container: ContainerProxy = current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER]
    if not container:
        return jsonify({"error": "Chat history not enabled"}), 400

    entra_oid = auth_claims.get("oid")
    if not entra_oid:
        return jsonify({"error": "User OID not found"}), 401

    try:
        res = container.query_items(
            query="SELECT * FROM c WHERE c.session_id = @session_id AND c.type = @type",
            parameters=[dict(name="@session_id", value=session_id), dict(name="@type", value="message_pair")],
            partition_key=[entra_oid, session_id],
        )

        message_pairs = []
        async for page in res.by_page():
            async for item in page:
                message_pairs.append([item["question"], item["response"]])

        return (
            jsonify(
                {
                    "id": session_id,
                    "entra_oid": entra_oid,
                    "answers": message_pairs,
                }
            ),
            200,
        )
    except Exception as error:
        return error_response(error, f"/chat_history/sessions/{session_id}")


@chat_history_cosmosdb_bp.delete("/chat_history/sessions/<session_id>")
@authenticated
async def delete_chat_history_session(auth_claims: dict[str, Any], session_id: str):
    if not current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED]:
        return jsonify({"error": "Chat history not enabled"}), 400

    container: ContainerProxy = current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER]
    if not container:
        return jsonify({"error": "Chat history not enabled"}), 400

    entra_oid = auth_claims.get("oid")
    if not entra_oid:
        return jsonify({"error": "User OID not found"}), 401

    try:
        res = container.query_items(
            query="SELECT c.id FROM c WHERE c.session_id = @session_id",
            parameters=[dict(name="@session_id", value=session_id)],
            partition_key=[entra_oid, session_id],
        )

        ids_to_delete = []
        async for page in res.by_page():
            async for item in page:
                ids_to_delete.append(item["id"])

        batch_operations = [("delete", (id,)) for id in ids_to_delete]
        await container.execute_item_batch(batch_operations=batch_operations, partition_key=[entra_oid, session_id])
        return await make_response("", 204)
    except Exception as error:
        return error_response(error, f"/chat_history/sessions/{session_id}")


@chat_history_cosmosdb_bp.post("/feedback")
@rate_limit(10, timedelta(minutes=1))  # 10 feedback submissions per minute per user
@authenticated
async def add_feedback(auth_claims: dict[str, Any]):
    """Add user feedback for a specific chat message."""
    if not current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED]:
        return jsonify({"error": "Chat history not enabled"}), 400

    feedback_container: ContainerProxy = current_app.config[CONFIG_COSMOS_FEEDBACK_CONTAINER]
    if not feedback_container:
        return jsonify({"error": "User feedback not configured. Set AZURE_USER_FEEDBACK_CONTAINER environment variable."}), 400

    entra_oid = auth_claims.get("oid")
    if not entra_oid:
        return jsonify({"error": "User OID not found"}), 401

    try:
        request_json = await request.get_json()
        session_id = request_json.get("sessionId")
        message_id = request_json.get("messageId")
        rating = request_json.get("rating")
        comment = request_json.get("comment", "")
        
        # Validate required fields
        if not session_id or not message_id or rating is None:
            return jsonify({"error": "sessionId, messageId, and rating are required"}), 400
        
        # Validate rating range
        if not isinstance(rating, (int, float)) or rating < 1 or rating > 5:
            return jsonify({"error": "Rating must be a number between 1 and 5"}), 400
        
        # Validate comment length
        if comment and len(comment) > 1000:
            return jsonify({"error": "Comment must be 1000 characters or less"}), 400
        
        # Validate messageId format
        if not message_id.startswith(session_id):
            return jsonify({"error": "Invalid messageId format"}), 400

        timestamp = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
        feedback_id = f"{message_id}-feedback"

        feedback_item = {
            "id": feedback_id,
            "sessionId": session_id,
            "messageId": message_id,
            "userId": entra_oid,
            "version": current_app.config[CONFIG_COSMOS_HISTORY_VERSION],
            "type": "feedback",
            "timestamp": timestamp,
            "rating": rating,
        }
        
        # Add comment if provided
        if comment:
            feedback_item["comment"] = comment

        # Use partition key [userId, sessionId] for the feedback container
        await feedback_container.upsert_item(feedback_item, partition_key=[entra_oid, session_id])
        
        return jsonify({"id": feedback_id, "message": "Feedback saved successfully"}), 201
    except Exception as error:
        return error_response(error, "/feedback")


@chat_history_cosmosdb_bp.get("/feedback/message/<message_id>")
@authenticated
async def get_feedback_by_message_id(auth_claims: dict[str, Any], message_id: str):
    """Get feedback for a specific message."""
    if not current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED]:
        return jsonify({"error": "Chat history not enabled"}), 400

    feedback_container: ContainerProxy = current_app.config[CONFIG_COSMOS_FEEDBACK_CONTAINER]
    if not feedback_container:
        return jsonify({"error": "User feedback not configured. Set AZURE_USER_FEEDBACK_CONTAINER environment variable."}), 400

    entra_oid = auth_claims.get("oid")
    if not entra_oid:
        return jsonify({"error": "User OID not found"}), 401

    try:
        # Extract session_id from message_id (format: session_id-index)
        session_id = message_id.rsplit('-', 1)[0]
        
        res = feedback_container.query_items(
            query="SELECT * FROM c WHERE c.messageId = @message_id AND c.userId = @user_id",
            parameters=[
                dict(name="@message_id", value=message_id),
                dict(name="@user_id", value=entra_oid)
            ],
            partition_key=[entra_oid, session_id],
        )

        feedback_items = []
        async for page in res.by_page():
            async for item in page:
                feedback_items.append({
                    "id": item["id"],
                    "sessionId": item["sessionId"],
                    "messageId": item["messageId"],
                    "rating": item["rating"],
                    "comment": item.get("comment", ""),
                    "timestamp": item["timestamp"]
                })

        return jsonify({"feedback": feedback_items}), 200
    except Exception as error:
        return error_response(error, f"/feedback/message/{message_id}")


@chat_history_cosmosdb_bp.get("/feedback/session/<session_id>")
@authenticated
async def get_feedback_by_session_id(auth_claims: dict[str, Any], session_id: str):
    """Get all feedback for a specific session."""
    if not current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED]:
        return jsonify({"error": "Chat history not enabled"}), 400

    feedback_container: ContainerProxy = current_app.config[CONFIG_COSMOS_FEEDBACK_CONTAINER]
    if not feedback_container:
        return jsonify({"error": "User feedback not configured. Set AZURE_USER_FEEDBACK_CONTAINER environment variable."}), 400

    entra_oid = auth_claims.get("oid")
    if not entra_oid:
        return jsonify({"error": "User OID not found"}), 401

    try:
        res = feedback_container.query_items(
            query="SELECT * FROM c WHERE c.sessionId = @session_id AND c.userId = @user_id ORDER BY c.timestamp ASC",
            parameters=[
                dict(name="@session_id", value=session_id),
                dict(name="@user_id", value=entra_oid)
            ],
            partition_key=[entra_oid, session_id],
        )

        feedback_items = []
        async for page in res.by_page():
            async for item in page:
                feedback_items.append({
                    "id": item["id"],
                    "sessionId": item["sessionId"],
                    "messageId": item["messageId"],
                    "rating": item["rating"],
                    "comment": item.get("comment", ""),
                    "timestamp": item["timestamp"]
                })

        return jsonify({"feedback": feedback_items}), 200
    except Exception as error:
        return error_response(error, f"/feedback/session/{session_id}")


@chat_history_cosmosdb_bp.put("/feedback/<feedback_id>")
@rate_limit(5, timedelta(minutes=1))  # 5 feedback updates per minute per user
@authenticated
async def update_feedback(auth_claims: dict[str, Any], feedback_id: str):
    """Update existing feedback."""
    if not current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED]:
        return jsonify({"error": "Chat history not enabled"}), 400

    feedback_container: ContainerProxy = current_app.config[CONFIG_COSMOS_FEEDBACK_CONTAINER]
    if not feedback_container:
        return jsonify({"error": "User feedback not configured. Set AZURE_USER_FEEDBACK_CONTAINER environment variable."}), 400

    entra_oid = auth_claims.get("oid")
    if not entra_oid:
        return jsonify({"error": "User OID not found"}), 401

    try:
        request_json = await request.get_json()
        rating = request_json.get("rating")
        comment = request_json.get("comment", "")
        
        # Validate rating if provided
        if rating is not None and (not isinstance(rating, (int, float)) or rating < 1 or rating > 5):
            return jsonify({"error": "Rating must be a number between 1 and 5"}), 400
        
        # Validate comment length
        if comment and len(comment) > 1000:
            return jsonify({"error": "Comment must be 1000 characters or less"}), 400

        # Extract session_id from feedback_id (format: session_id-index-feedback)
        message_id = feedback_id.replace('-feedback', '')
        session_id = message_id.rsplit('-', 1)[0]
        
        # First, get the existing feedback item
        try:
            existing_item = await feedback_container.read_item(
                item=feedback_id,
                partition_key=[entra_oid, session_id]
            )
        except Exception:
            return jsonify({"error": "Feedback not found"}), 404
        
        # Verify ownership
        if existing_item.get("userId") != entra_oid:
            return jsonify({"error": "Unauthorized"}), 403
        
        # Update fields
        if rating is not None:
            existing_item["rating"] = rating
        if comment is not None:
            existing_item["comment"] = comment
        
        # Update timestamp
        existing_item["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S.%fZ", time.gmtime())
        
        # Save updated item
        await feedback_container.upsert_item(existing_item, partition_key=[entra_oid, session_id])
        
        return jsonify({"message": "Feedback updated successfully"}), 200
    except Exception as error:
        return error_response(error, f"/feedback/{feedback_id}")


@chat_history_cosmosdb_bp.before_app_serving
async def setup_clients():
    USE_CHAT_HISTORY_COSMOS = os.getenv("USE_CHAT_HISTORY_COSMOS", "").lower() == "true"
    AZURE_COSMOSDB_ACCOUNT = os.getenv("AZURE_COSMOSDB_ACCOUNT")
    AZURE_CHAT_HISTORY_DATABASE = os.getenv("AZURE_CHAT_HISTORY_DATABASE")
    AZURE_CHAT_HISTORY_CONTAINER = os.getenv("AZURE_CHAT_HISTORY_CONTAINER")
    AZURE_USER_FEEDBACK_CONTAINER = os.getenv("AZURE_USER_FEEDBACK_CONTAINER")

    azure_credential: Union[AzureDeveloperCliCredential, ManagedIdentityCredential] = current_app.config[
        CONFIG_CREDENTIAL
    ]

    if USE_CHAT_HISTORY_COSMOS:
        current_app.logger.info("USE_CHAT_HISTORY_COSMOS is true, setting up CosmosDB client")
        if not AZURE_COSMOSDB_ACCOUNT:
            raise ValueError("AZURE_COSMOSDB_ACCOUNT must be set when USE_CHAT_HISTORY_COSMOS is true")
        if not AZURE_CHAT_HISTORY_DATABASE:
            raise ValueError("AZURE_CHAT_HISTORY_DATABASE must be set when USE_CHAT_HISTORY_COSMOS is true")
        if not AZURE_CHAT_HISTORY_CONTAINER:
            raise ValueError("AZURE_CHAT_HISTORY_CONTAINER must be set when USE_CHAT_HISTORY_COSMOS is true")

        cosmos_client = CosmosClient(f"https://{AZURE_COSMOSDB_ACCOUNT}.documents.azure.com:443/", azure_credential)
        current_app.config[CONFIG_COSMOS_HISTORY_CLIENT] = cosmos_client

        cosmos_db = cosmos_client.get_database_client(AZURE_CHAT_HISTORY_DATABASE)
        container = cosmos_db.get_container_client(AZURE_CHAT_HISTORY_CONTAINER)
        current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER] = container

        # Initialize UserFeedback container if configured (optional for backward compatibility)
        if AZURE_USER_FEEDBACK_CONTAINER:
            current_app.logger.info(f"Setting up UserFeedback container: {AZURE_USER_FEEDBACK_CONTAINER}")
            feedback_container = cosmos_db.get_container_client(AZURE_USER_FEEDBACK_CONTAINER)
            current_app.config[CONFIG_COSMOS_FEEDBACK_CONTAINER] = feedback_container
        else:
            current_app.logger.info("AZURE_USER_FEEDBACK_CONTAINER not configured, feedback endpoints will be disabled")
            current_app.config[CONFIG_COSMOS_FEEDBACK_CONTAINER] = None

        current_app.config[CONFIG_COSMOS_HISTORY_VERSION] = os.environ["AZURE_CHAT_HISTORY_VERSION"]

    else:
        current_app.config[CONFIG_CHAT_HISTORY_COSMOS_ENABLED] = False


@chat_history_cosmosdb_bp.after_app_serving
async def close_clients():
    if current_app.config.get(CONFIG_COSMOS_HISTORY_CLIENT):
        cosmos_client: CosmosClient = current_app.config[CONFIG_COSMOS_HISTORY_CLIENT]
        await cosmos_client.close()
