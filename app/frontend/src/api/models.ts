export const enum RetrievalMode {
    Hybrid = "hybrid",
    Vectors = "vectors",
    Text = "text"
}

export const enum GPT4VInput {
    TextAndImages = "textAndImages",
    Images = "images",
    Texts = "texts"
}

export const enum VectorFields {
    Embedding = "textEmbeddingOnly",
    ImageEmbedding = "imageEmbeddingOnly",
    TextAndImageEmbeddings = "textAndImageEmbeddings"
}

// Advanced citation strategy types
export type CitationAuthenticationInfo = {
    type: string;
    requiresAuth: boolean;
    additionalHeaders?: Record<string, string>;
};

export type CitationStrategyInfo = {
    name: string;
    type: string;
    baseUrl: string;
    description?: string;
    enabled: boolean;
    priority: number;
    fileExtensions?: string[];
    pathPatterns?: string[];
    authentication?: CitationAuthenticationInfo;
};

export type CitationStrategiesConfig = {
    version: string;
    defaultStrategy?: string;
    fallbackStrategy?: string;
    legacyBaseUrl?: string;
    strategies: CitationStrategyInfo[];
};

export type CitationResult = {
    url: string;
    strategyUsed: string;
    requiresAuth: boolean;
    authHeaders?: Record<string, string>;
    metadata?: Record<string, any>;
    error?: string;
};

export type ChatAppRequestOverrides = {
    retrieval_mode?: RetrievalMode;
    semantic_ranker?: boolean;
    semantic_captions?: boolean;
    query_rewriting?: boolean;
    reasoning_effort?: string;
    include_category?: string;
    exclude_category?: string;
    seed?: number;
    top?: number;
    max_subqueries?: number;
    results_merge_strategy?: string;
    temperature?: number;
    minimum_search_score?: number;
    minimum_reranker_score?: number;
    prompt_template?: string;
    prompt_template_prefix?: string;
    prompt_template_suffix?: string;
    suggest_followup_questions?: boolean;
    use_oid_security_filter?: boolean;
    use_groups_security_filter?: boolean;
    use_gpt4v?: boolean;
    gpt4v_input?: GPT4VInput;
    vector_fields: VectorFields;
    language: string;
    use_agentic_retrieval: boolean;
};

export type ResponseMessage = {
    content: string;
    role: string;
};

export type Thoughts = {
    title: string;
    description: any; // It can be any output from the api
    props?: { [key: string]: any };
};

export type ResponseContext = {
    data_points: string[];
    followup_questions: string[] | null;
    thoughts: Thoughts[];
};

export type ChatAppResponseOrError = {
    message: ResponseMessage;
    delta: ResponseMessage;
    context: ResponseContext;
    session_state: any;
    error?: string;
};

export type ChatAppResponse = {
    message: ResponseMessage;
    delta: ResponseMessage;
    context: ResponseContext;
    session_state: any;
};

export type ChatAppRequestContext = {
    overrides?: ChatAppRequestOverrides;
};

export type ChatAppRequest = {
    messages: ResponseMessage[];
    context?: ChatAppRequestContext;
    session_state: any;
};

export type Config = {
    defaultReasoningEffort: string;
    showGPT4VOptions: boolean;
    showSemanticRankerOption: boolean;
    showQueryRewritingOption: boolean;
    showReasoningEffortOption: boolean;
    streamingEnabled: boolean;
    showVectorOption: boolean;
    showUserUpload: boolean;
    showLanguagePicker: boolean;
    showSpeechInput: boolean;
    showSpeechOutputBrowser: boolean;
    showSpeechOutputAzure: boolean;
    showChatHistoryBrowser: boolean;
    showChatHistoryCosmos: boolean;
    showAgenticRetrievalOption: boolean;
    citationBaseUrl?: string;
    citationStrategies?: CitationStrategiesConfig;
};

export type SimpleAPIResponse = {
    message?: string;
};

export interface SpeechConfig {
    speechUrls: (string | null)[];
    setSpeechUrls: (urls: (string | null)[]) => void;
    audio: HTMLAudioElement;
    isPlaying: boolean;
    setIsPlaying: (isPlaying: boolean) => void;
}

export type HistoryListApiResponse = {
    sessions: {
        id: string;
        entra_oid: string;
        title: string;
        timestamp: number;
    }[];
    continuation_token?: string;
};

export type HistoryApiResponse = {
    id: string;
    entra_oid: string;
    messages: {
        messageId: string;
        question: string;
        response: string;
    }[];
};

export type FeedbackRequest = {
    sessionId: string;
    messageId: string;
    rating: number;
    comment?: string;
};

export type FeedbackResponse = {
    id: string;
    message: string;
};

export type FeedbackData = {
    id: string;
    sessionId: string;
    messageId: string;
    rating: number;
    comment?: string;
    timestamp: string;
};

export type FeedbackApiResponse = {
    feedback: FeedbackData[];
};
