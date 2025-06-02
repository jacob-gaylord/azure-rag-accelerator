import { IHistoryProvider, Answers, HistoryProviderOptions, HistoryMetaData } from "./IProvider";
import { deleteChatHistoryApi, getChatHistoryApi, getChatHistoryListApi, postChatHistoryApi } from "../../api";
import { ChatAppResponse } from "../../api";

export class CosmosDBProvider implements IHistoryProvider {
    getProviderName = () => HistoryProviderOptions.CosmosDB;

    private continuationToken: string | undefined;
    private isItemEnd: boolean = false;

    resetContinuationToken() {
        this.continuationToken = undefined;
        this.isItemEnd = false;
    }

    async getNextItems(count: number, idToken?: string): Promise<HistoryMetaData[]> {
        if (this.isItemEnd) {
            return [];
        }

        try {
            const response = await getChatHistoryListApi(count, this.continuationToken, idToken || "");
            this.continuationToken = response.continuation_token;
            if (!this.continuationToken) {
                this.isItemEnd = true;
            }
            return response.sessions.map(session => ({
                id: session.id,
                title: session.title,
                timestamp: session.timestamp
            }));
        } catch (e) {
            console.error(e);
            return [];
        }
    }

    async addItem(id: string, answers: Answers, idToken?: string): Promise<void> {
        await postChatHistoryApi({ id, answers }, idToken || "");
        return;
    }

    async getItem(id: string, idToken?: string): Promise<Answers | null> {
        const response = await getChatHistoryApi(id, idToken || "");
        
        // Handle new structured format with messages
        if (response.messages && Array.isArray(response.messages)) {
            // Convert structured messages to Answers format for backward compatibility
            const answers: Answers = response.messages.map(msg => {
                // Parse the response field if it's a string, otherwise assume it's already a ChatAppResponse
                let chatResponse: ChatAppResponse;
                if (typeof msg.response === 'string') {
                    try {
                        chatResponse = JSON.parse(msg.response);
                    } catch (e) {
                        // If parsing fails, create a basic ChatAppResponse structure
                        chatResponse = {
                            message: { content: msg.response, role: "assistant" },
                            delta: { content: "", role: "assistant" },
                            context: { data_points: [], followup_questions: null, thoughts: [] },
                            session_state: null
                        };
                    }
                } else {
                    chatResponse = msg.response as ChatAppResponse;
                }
                
                return [msg.question, chatResponse] as [string, ChatAppResponse];
            });
            return answers;
        }
        
        // Return null if no messages found
        return null;
    }

    async deleteItem(id: string, idToken?: string): Promise<void> {
        await deleteChatHistoryApi(id, idToken || "");
        return;
    }
}
