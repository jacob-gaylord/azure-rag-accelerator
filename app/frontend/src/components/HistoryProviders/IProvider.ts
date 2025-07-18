import { ChatAppResponse } from "../../api";

export type HistoryMetaData = { id: string; title: string; timestamp: number };
export type Answers = [user: string, response: ChatAppResponse][];

export const enum HistoryProviderOptions {
    None = "none",
    IndexedDB = "indexedDB",
    CosmosDB = "cosmosDB"
}

export type FeedbackData = Record<string, { type: "positive" | "negative"; comment?: string; timestamp?: string }>;

export interface IHistoryProvider {
    getProviderName(): HistoryProviderOptions;
    resetContinuationToken(): void;
    getNextItems(count: number, idToken?: string): Promise<HistoryMetaData[]>;
    addItem(id: string, answers: Answers, idToken?: string, feedback?: FeedbackData): Promise<void>;
    getItem(id: string, idToken?: string): Promise<Answers | null>;
    deleteItem(id: string, idToken?: string): Promise<void>;
}
