const BACKEND_URI = "";

import {
    ChatAppResponse,
    ChatAppResponseOrError,
    ChatAppRequest,
    Config,
    SimpleAPIResponse,
    HistoryListApiResponse,
    HistoryApiResponse,
    FeedbackRequest,
    FeedbackResponse,
    FeedbackApiResponse,
    CitationStrategiesConfig,
    CitationStrategyInfo,
    CitationResult
} from "./models";
import { useLogin, getToken, isUsingAppServicesLogin } from "../authConfig";

export async function getHeaders(idToken: string | undefined): Promise<Record<string, string>> {
    // If using login and not using app services, add the id token of the logged in account as the authorization
    if (useLogin && !isUsingAppServicesLogin) {
        if (idToken) {
            return { Authorization: `Bearer ${idToken}` };
        }
    }

    return {};
}

export async function configApi(): Promise<Config> {
    const response = await fetch(`${BACKEND_URI}/config`, {
        method: "GET"
    });

    return (await response.json()) as Config;
}

export async function askApi(request: ChatAppRequest, idToken: string | undefined): Promise<ChatAppResponse> {
    const headers = await getHeaders(idToken);
    const response = await fetch(`${BACKEND_URI}/ask`, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(request)
    });

    if (response.status > 299 || !response.ok) {
        throw Error(`Request failed with status ${response.status}`);
    }
    const parsedResponse: ChatAppResponseOrError = await response.json();
    if (parsedResponse.error) {
        throw Error(parsedResponse.error);
    }

    return parsedResponse as ChatAppResponse;
}

export async function chatApi(request: ChatAppRequest, shouldStream: boolean, idToken: string | undefined): Promise<Response> {
    let url = `${BACKEND_URI}/chat`;
    if (shouldStream) {
        url += "/stream";
    }
    const headers = await getHeaders(idToken);
    return await fetch(url, {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(request)
    });
}

export async function getSpeechApi(text: string): Promise<string | null> {
    return await fetch("/speech", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            text: text
        })
    })
        .then(response => {
            if (response.status == 200) {
                return response.blob();
            } else if (response.status == 400) {
                console.log("Speech synthesis is not enabled.");
                return null;
            } else {
                console.error("Unable to get speech synthesis.");
                return null;
            }
        })
        .then(blob => (blob ? URL.createObjectURL(blob) : null));
}

export function getCitationFilePath(citation: string, citationBaseUrl?: string): string {
    // If a custom base URL is provided, use it; otherwise use the current backend
    if (citationBaseUrl && citationBaseUrl.trim() !== "") {
        // Remove trailing slash from base URL and leading slash from citation if both exist
        const baseUrl = citationBaseUrl.replace(/\/+$/, "");
        const path = citation.startsWith("/") ? citation : `/${citation}`;
        return `${baseUrl}${path}`;
    }

    // Default behavior - use the current backend's /content endpoint
    return `${BACKEND_URI}/content/${citation}`;
}

/**
 * Generate a citation URL using advanced citation strategies
 */
export function generateCitationUrl(citation: string, config?: Config, metadata?: Record<string, any>): CitationResult {
    // If no config or citation strategies available, fall back to legacy behavior
    if (!config?.citationStrategies) {
        const url = getCitationFilePath(citation, config?.citationBaseUrl);
        return {
            url,
            strategyUsed: "legacy",
            requiresAuth: false,
            metadata: { source: "legacy_fallback" }
        };
    }

    const strategies = config.citationStrategies;

    try {
        // Find the best strategy for this citation
        const bestStrategy = findBestCitationStrategy(citation, strategies);

        if (!bestStrategy) {
            // Fall back to legacy or default strategy
            const fallbackUrl = strategies.legacyBaseUrl
                ? getCitationFilePath(citation, strategies.legacyBaseUrl)
                : getCitationFilePath(citation, config.citationBaseUrl);

            return {
                url: fallbackUrl,
                strategyUsed: "fallback",
                requiresAuth: false,
                metadata: { source: "fallback" }
            };
        }

        // Generate URL using the selected strategy
        const url = buildCitationUrl(citation, bestStrategy);

        return {
            url,
            strategyUsed: bestStrategy.name,
            requiresAuth: bestStrategy.authentication?.requiresAuth || false,
            authHeaders: bestStrategy.authentication?.additionalHeaders,
            metadata: {
                strategyType: bestStrategy.type,
                strategyPriority: bestStrategy.priority,
                originalCitation: citation,
                ...metadata
            }
        };
    } catch (error) {
        // Error handling - fall back to legacy behavior
        const fallbackUrl = getCitationFilePath(citation, config?.citationBaseUrl);
        return {
            url: fallbackUrl,
            strategyUsed: "error_fallback",
            requiresAuth: false,
            error: error instanceof Error ? error.message : "Unknown error",
            metadata: { source: "error_fallback" }
        };
    }
}

/**
 * Find the best citation strategy for a given file path
 */
function findBestCitationStrategy(filePath: string, strategiesConfig: CitationStrategiesConfig): CitationStrategyInfo | null {
    const availableStrategies = strategiesConfig.strategies.filter(s => s.enabled);

    if (availableStrategies.length === 0) {
        return null;
    }

    // Check if there's a specific default strategy
    if (strategiesConfig.defaultStrategy) {
        const defaultStrategy = availableStrategies.find(s => s.name === strategiesConfig.defaultStrategy);
        if (defaultStrategy && canStrategyHandleFile(filePath, defaultStrategy)) {
            return defaultStrategy;
        }
    }

    // Find all strategies that can handle this file
    const suitableStrategies = availableStrategies.filter(strategy => canStrategyHandleFile(filePath, strategy));

    if (suitableStrategies.length === 0) {
        // Try fallback strategy if specified
        if (strategiesConfig.fallbackStrategy) {
            const fallbackStrategy = availableStrategies.find(s => s.name === strategiesConfig.fallbackStrategy);
            if (fallbackStrategy) {
                return fallbackStrategy;
            }
        }
        return null;
    }

    // Sort by priority (higher priority first) and return the best match
    suitableStrategies.sort((a, b) => b.priority - a.priority);
    return suitableStrategies[0];
}

/**
 * Check if a strategy can handle a specific file
 */
function canStrategyHandleFile(filePath: string, strategy: CitationStrategyInfo): boolean {
    // Check file extensions if specified
    if (strategy.fileExtensions && strategy.fileExtensions.length > 0) {
        const fileExt = filePath.split(".").pop()?.toLowerCase();
        if (!fileExt || !strategy.fileExtensions.some(ext => ext.toLowerCase().replace(".", "") === fileExt)) {
            return false;
        }
    }

    // Check path patterns if specified
    if (strategy.pathPatterns && strategy.pathPatterns.length > 0) {
        const matchesPattern = strategy.pathPatterns.some(pattern => {
            // Simple pattern matching (can be enhanced for more complex patterns)
            if (pattern.includes("*")) {
                const regex = new RegExp("^" + pattern.replace(/\*/g, ".*") + "$", "i");
                return regex.test(filePath);
            } else {
                return filePath.toLowerCase().includes(pattern.toLowerCase());
            }
        });

        if (!matchesPattern) {
            return false;
        }
    }

    return true;
}

/**
 * Build citation URL using a specific strategy
 */
function buildCitationUrl(filePath: string, strategy: CitationStrategyInfo): string {
    let baseUrl = strategy.baseUrl.replace(/\/+$/, ""); // Remove trailing slashes
    let path = filePath.startsWith("/") ? filePath.slice(1) : filePath; // Remove leading slash

    // Handle special cases for different strategy types
    switch (strategy.type) {
        case "sharepoint":
            // SharePoint URLs might need special handling
            return `${baseUrl}/${path}`;

        case "blob_storage":
            // Azure Blob Storage URLs
            return `${baseUrl}/${path}`;

        case "file_server":
            // Traditional file server URLs
            return `${baseUrl}/${path}`;

        case "cms":
            // CMS systems might use document IDs instead of paths
            const docId = path.split(".")[0]; // Remove extension for CMS
            return `${baseUrl}/documents/${docId}`;

        case "custom_url":
            // Custom URL with potential template support
            return `${baseUrl}/${path}`;

        default:
            // Default strategy
            if (baseUrl) {
                return `${baseUrl}/${path}`;
            } else {
                return `${BACKEND_URI}/content/${path}`;
            }
    }
}

/**
 * Enhanced citation path function that supports advanced strategies
 */
export function getAdvancedCitationFilePath(citation: string, config?: Config, metadata?: Record<string, any>): string {
    const result = generateCitationUrl(citation, config, metadata);
    return result.url;
}

/**
 * Get citation information including authentication requirements
 */
export function getCitationInfo(citation: string, config?: Config, metadata?: Record<string, any>): CitationResult {
    return generateCitationUrl(citation, config, metadata);
}

export async function uploadFileApi(request: FormData, idToken: string): Promise<SimpleAPIResponse> {
    const response = await fetch("/upload", {
        method: "POST",
        headers: await getHeaders(idToken),
        body: request
    });

    if (!response.ok) {
        throw new Error(`Uploading files failed: ${response.statusText}`);
    }

    const dataResponse: SimpleAPIResponse = await response.json();
    return dataResponse;
}

export async function deleteUploadedFileApi(filename: string, idToken: string): Promise<SimpleAPIResponse> {
    const headers = await getHeaders(idToken);
    const response = await fetch("/delete_uploaded", {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ filename })
    });

    if (!response.ok) {
        throw new Error(`Deleting file failed: ${response.statusText}`);
    }

    const dataResponse: SimpleAPIResponse = await response.json();
    return dataResponse;
}

export async function listUploadedFilesApi(idToken: string): Promise<string[]> {
    const response = await fetch(`/list_uploaded`, {
        method: "GET",
        headers: await getHeaders(idToken)
    });

    if (!response.ok) {
        throw new Error(`Listing files failed: ${response.statusText}`);
    }

    const dataResponse: string[] = await response.json();
    return dataResponse;
}

export async function postChatHistoryApi(item: any, idToken: string): Promise<any> {
    const headers = await getHeaders(idToken);
    const response = await fetch("/chat_history", {
        method: "POST",
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify(item)
    });

    if (!response.ok) {
        throw new Error(`Posting chat history failed: ${response.statusText}`);
    }

    const dataResponse: any = await response.json();
    return dataResponse;
}

export async function getChatHistoryListApi(count: number, continuationToken: string | undefined, idToken: string): Promise<HistoryListApiResponse> {
    const headers = await getHeaders(idToken);
    let url = `${BACKEND_URI}/chat_history/sessions?count=${count}`;
    if (continuationToken) {
        url += `&continuationToken=${continuationToken}`;
    }

    const response = await fetch(url.toString(), {
        method: "GET",
        headers: { ...headers, "Content-Type": "application/json" }
    });

    if (!response.ok) {
        throw new Error(`Getting chat histories failed: ${response.statusText}`);
    }

    const dataResponse: HistoryListApiResponse = await response.json();
    return dataResponse;
}

export async function getChatHistoryApi(id: string, idToken: string): Promise<HistoryApiResponse> {
    const headers = await getHeaders(idToken);
    const response = await fetch(`/chat_history/sessions/${id}`, {
        method: "GET",
        headers: { ...headers, "Content-Type": "application/json" }
    });

    if (!response.ok) {
        throw new Error(`Getting chat history failed: ${response.statusText}`);
    }

    const dataResponse: HistoryApiResponse = await response.json();
    return dataResponse;
}

export async function deleteChatHistoryApi(id: string, idToken: string): Promise<any> {
    const headers = await getHeaders(idToken);
    const response = await fetch(`/chat_history/sessions/${id}`, {
        method: "DELETE",
        headers: { ...headers, "Content-Type": "application/json" }
    });

    if (!response.ok) {
        throw new Error(`Deleting chat history failed: ${response.statusText}`);
    }
}

export async function submitFeedbackApi(request: FeedbackRequest, idToken: string): Promise<FeedbackResponse> {
    try {
        const headers = await getHeaders(idToken);
        const response = await fetch(`${BACKEND_URI}/feedback`, {
            method: "POST",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            // Handle specific error cases
            if (response.status === 429) {
                throw new Error("Rate limit exceeded. Please wait a moment before submitting feedback again.");
            } else if (response.status === 401) {
                throw new Error("Authentication required. Please log in again.");
            } else if (response.status === 400) {
                // Try to get the specific error message from the response
                try {
                    const errorData = await response.json();
                    throw new Error(errorData.error || "Invalid feedback data. Please check your input.");
                } catch {
                    throw new Error("Invalid feedback data. Please check your input.");
                }
            } else if (response.status === 404) {
                throw new Error("Message not found. This feedback cannot be submitted.");
            } else if (response.status >= 500) {
                throw new Error("Server error. Please try again later.");
            } else {
                throw new Error(`Submitting feedback failed: ${response.statusText}`);
            }
        }

        const dataResponse: FeedbackResponse = await response.json();
        return dataResponse;
    } catch (error) {
        // Handle network errors
        if (error instanceof TypeError && error.message.includes("fetch")) {
            throw new Error("Network error. Please check your connection and try again.");
        }
        // Re-throw other errors as-is
        throw error;
    }
}

export async function getFeedbackByMessageApi(messageId: string, idToken: string): Promise<FeedbackApiResponse> {
    try {
        const headers = await getHeaders(idToken);
        const response = await fetch(`${BACKEND_URI}/feedback/message/${messageId}`, {
            method: "GET",
            headers: { ...headers, "Content-Type": "application/json" }
        });

        if (!response.ok) {
            // Handle specific error cases
            if (response.status === 429) {
                throw new Error("Rate limit exceeded. Please wait a moment before trying again.");
            } else if (response.status === 401) {
                throw new Error("Authentication required. Please log in again.");
            } else if (response.status === 404) {
                throw new Error("Message not found or no feedback available.");
            } else if (response.status >= 500) {
                throw new Error("Server error. Please try again later.");
            } else {
                throw new Error(`Getting feedback failed: ${response.statusText}`);
            }
        }

        const dataResponse: FeedbackApiResponse = await response.json();
        return dataResponse;
    } catch (error) {
        // Handle network errors
        if (error instanceof TypeError && error.message.includes("fetch")) {
            throw new Error("Network error. Please check your connection and try again.");
        }
        // Re-throw other errors as-is
        throw error;
    }
}

export async function updateFeedbackApi(feedbackId: string, request: Partial<FeedbackRequest>, idToken: string): Promise<{ message: string }> {
    try {
        const headers = await getHeaders(idToken);
        const response = await fetch(`${BACKEND_URI}/feedback/${feedbackId}`, {
            method: "PUT",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify(request)
        });

        if (!response.ok) {
            // Handle specific error cases
            if (response.status === 429) {
                throw new Error("Rate limit exceeded. Please wait a moment before updating feedback again.");
            } else if (response.status === 401) {
                throw new Error("Authentication required. Please log in again.");
            } else if (response.status === 400) {
                // Try to get the specific error message from the response
                try {
                    const errorData = await response.json();
                    throw new Error(errorData.error || "Invalid feedback data. Please check your input.");
                } catch {
                    throw new Error("Invalid feedback data. Please check your input.");
                }
            } else if (response.status === 403) {
                throw new Error("You don't have permission to update this feedback.");
            } else if (response.status === 404) {
                throw new Error("Feedback not found. It may have been deleted.");
            } else if (response.status >= 500) {
                throw new Error("Server error. Please try again later.");
            } else {
                throw new Error(`Updating feedback failed: ${response.statusText}`);
            }
        }

        const dataResponse: { message: string } = await response.json();
        return dataResponse;
    } catch (error) {
        // Handle network errors
        if (error instanceof TypeError && error.message.includes("fetch")) {
            throw new Error("Network error. Please check your connection and try again.");
        }
        // Re-throw other errors as-is
        throw error;
    }
}
