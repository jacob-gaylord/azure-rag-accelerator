import os
import time
from datetime import datetime
from typing import Any, Union

from azure.cosmos.aio import ContainerProxy, CosmosClient
from azure.identity.aio import AzureDeveloperCliCredential, ManagedIdentityCredential
from quart import Blueprint, current_app, jsonify, make_response, request

from config import (
    CONFIG_CHAT_HISTORY_COSMOS_ENABLED,
    CONFIG_COSMOS_HISTORY_CLIENT,
    CONFIG_COSMOS_HISTORY_CONTAINER,
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
        feedback_data = request_json.get("feedback", {})  # Get feedback data if provided
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
            message_item = {
                "id": f"{session_id}-{ind}",
                "version": current_app.config[CONFIG_COSMOS_HISTORY_VERSION],
                "session_id": session_id,
                "entra_oid": entra_oid,
                "type": "message_pair",
                "question": message_pair[0],
                "response": message_pair[1],
            }
            
            # Add feedback if it exists for this message
            message_id = f"{session_id}-{ind}"
            if message_id in feedback_data:
                feedback = feedback_data[message_id]
                message_item["feedback"] = {
                    "type": feedback.get("type"),
                    "comment": feedback.get("comment", ""),
                    "timestamp": feedback.get("timestamp", datetime.utcnow().isoformat()),
                    "user_oid": entra_oid
                }
            
            message_pair_items.append(message_item)

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


@chat_history_cosmosdb_bp.before_app_serving
async def setup_clients():
    USE_CHAT_HISTORY_COSMOS = os.getenv("USE_CHAT_HISTORY_COSMOS", "").lower() == "true"
    AZURE_COSMOSDB_ACCOUNT = os.getenv("AZURE_COSMOSDB_ACCOUNT")
    AZURE_CHAT_HISTORY_DATABASE = os.getenv("AZURE_CHAT_HISTORY_DATABASE")
    AZURE_CHAT_HISTORY_CONTAINER = os.getenv("AZURE_CHAT_HISTORY_CONTAINER")

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
        cosmos_client = CosmosClient(
            url=f"https://{AZURE_COSMOSDB_ACCOUNT}.documents.azure.com:443/", credential=azure_credential
        )
        cosmos_db = cosmos_client.get_database_client(AZURE_CHAT_HISTORY_DATABASE)
        cosmos_container = cosmos_db.get_container_client(AZURE_CHAT_HISTORY_CONTAINER)

        current_app.config[CONFIG_COSMOS_HISTORY_CLIENT] = cosmos_client
        current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER] = cosmos_container
        current_app.config[CONFIG_COSMOS_HISTORY_VERSION] = os.environ["AZURE_CHAT_HISTORY_VERSION"]


async def save_feedback_to_cosmos(conversation_id: str, message_id: str, 
                              user_oid: str, feedback_type: str, feedback_comment: str):
    """Save user feedback for a specific message in a conversation"""
    try:
        container: ContainerProxy = current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER]
        if not container:
            raise ValueError("CosmosDB container not configured")
        
        # Find the specific message_pair item to update
        res = container.query_items(
            query="SELECT * FROM c WHERE c.session_id = @session_id AND c.type = @type AND c.id = @message_id",
            parameters=[
                dict(name="@session_id", value=conversation_id),
                dict(name="@type", value="message_pair"),
                dict(name="@message_id", value=message_id)
            ],
            partition_key=[user_oid, conversation_id],
        )
        
        message_item = None
        async for page in res.by_page():
            async for item in page:
                message_item = item
                break
        
        if not message_item:
            # Try alternative message ID format (session_id-index)
            res = container.query_items(
                query="SELECT * FROM c WHERE c.session_id = @session_id AND c.type = @type",
                parameters=[
                    dict(name="@session_id", value=conversation_id),
                    dict(name="@type", value="message_pair")
                ],
                partition_key=[user_oid, conversation_id],
            )
            
            async for page in res.by_page():
                async for item in page:
                    if item.get('id') == message_id:
                        message_item = item
                        break
        
        if not message_item:
            raise ValueError(f"Message {message_id} not found in conversation {conversation_id}")
        
        # Add feedback to the message
        message_item['feedback'] = {
            'type': feedback_type,
            'comment': feedback_comment,
            'timestamp': datetime.utcnow().isoformat(),
            'user_oid': user_oid
        }
        
        # Update the message in CosmosDB
        await container.upsert_item(message_item)
        
    except Exception as e:
        current_app.logger.exception(f"Error saving feedback: {e}")
        raise


async def soft_delete_conversation(conversation_id: str, user_oid: str):
    """Soft delete a conversation by marking it as deleted"""
    try:
        container: ContainerProxy = current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER]
        if not container:
            raise ValueError("CosmosDB container not configured")
        
        # Get the session item
        session_item = await container.read_item(
            item=conversation_id,
            partition_key=[user_oid, conversation_id]
        )
        
        # Mark as soft deleted
        session_item['is_deleted'] = True
        session_item['deleted_at'] = datetime.utcnow().isoformat()
        session_item['deleted_by'] = user_oid
        
        await container.upsert_item(session_item)
        
    except Exception as e:
        current_app.logger.exception(f"Error soft deleting conversation: {e}")
        raise


async def get_feedback_analytics():
    """Get feedback analytics for admin users"""
    try:
        container: ContainerProxy = current_app.config[CONFIG_COSMOS_HISTORY_CONTAINER]
        if not container:
            raise ValueError("CosmosDB container not configured")
        
        # Query for messages with feedback
        res = container.query_items(
            query="""
                SELECT 
                    c.feedback.type as feedback_type,
                    c.feedback.comment as feedback_comment,
                    c.feedback.timestamp as feedback_timestamp,
                    c.session_id,
                    c.question,
                    COUNT(1) as count
                FROM c 
                WHERE c.type = 'message_pair' 
                AND IS_DEFINED(c.feedback)
                GROUP BY c.feedback.type, c.feedback.comment, c.feedback.timestamp, c.session_id, c.question
            """,
            enable_cross_partition_query=True
        )
        
        analytics = {
            'total_feedback': 0,
            'positive_feedback': 0,
            'negative_feedback': 0,
            'recent_feedback': []
        }
        
        async for page in res.by_page():
            async for item in page:
                analytics['total_feedback'] += 1
                if item.get('feedback_type') == 'positive':
                    analytics['positive_feedback'] += 1
                elif item.get('feedback_type') == 'negative':
                    analytics['negative_feedback'] += 1
                
                analytics['recent_feedback'].append({
                    'type': item.get('feedback_type'),
                    'comment': item.get('feedback_comment'),
                    'timestamp': item.get('feedback_timestamp'),
                    'session_id': item.get('session_id'),
                    'question': item.get('question')
                })
        
        # Sort recent feedback by timestamp (most recent first)
        analytics['recent_feedback'].sort(
            key=lambda x: x['timestamp'] if x['timestamp'] else '',
            reverse=True
        )
        
        # Limit to 100 most recent
        analytics['recent_feedback'] = analytics['recent_feedback'][:100]
        
        return analytics
        
    except Exception as e:
        current_app.logger.exception(f"Error getting feedback analytics: {e}")
        raise


@chat_history_cosmosdb_bp.after_app_serving
async def close_clients():
    if current_app.config.get(CONFIG_COSMOS_HISTORY_CLIENT):
        cosmos_client: CosmosClient = current_app.config[CONFIG_COSMOS_HISTORY_CLIENT]
        await cosmos_client.close()
