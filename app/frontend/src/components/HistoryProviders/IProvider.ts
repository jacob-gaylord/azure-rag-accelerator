import { ChatAppResponse } from "../../api";

export type HistoryMetaData = { id: string; title: string; timestamp: number };
export type Answers = [user: string, response: ChatAppResponse][];

// New structured format with messageId
export type StructuredMessage = {
    messageId: string;
    question: string;
    response: string;
};
export type StructuredMessages = StructuredMessage[];

export const enum HistoryProviderOptions {
    None = "none",
    IndexedDB = "indexedDB",
    CosmosDB = "cosmosDB"
}

export interface IHistoryProvider {
    getProviderName(): HistoryProviderOptions;
    resetContinuationToken(): void;
    getNextItems(count: number, idToken?: string): Promise<HistoryMetaData[]>;
    addItem(id: string, answers: Answers, idToken?: string): Promise<void>;
    getItem(id: string, idToken?: string): Promise<Answers | null>;
    deleteItem(id: string, idToken?: string): Promise<void>;
}
