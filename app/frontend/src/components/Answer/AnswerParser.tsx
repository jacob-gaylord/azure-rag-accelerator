import { renderToStaticMarkup } from "react-dom/server";
import { ChatAppResponse, getCitationFilePath, getAdvancedCitationFilePath, getCitationInfo, Config, CitationResult } from "../../api";

type HtmlParsedAnswer = {
    answerHtml: string;
    citations: string[];
    citationInfo?: CitationResult[]; // Additional citation metadata
};

// Function to validate citation format and check if dataPoint starts with possible citation
function isCitationValid(contextDataPoints: any, citationCandidate: string): boolean {
    const regex = /.+\.\w{1,}(?:#\S*)?$/;
    if (!regex.test(citationCandidate)) {
        return false;
    }

    // Check if contextDataPoints is an object with a text property that is an array
    let dataPointsArray: string[];
    if (Array.isArray(contextDataPoints)) {
        dataPointsArray = contextDataPoints;
    } else if (contextDataPoints && Array.isArray(contextDataPoints.text)) {
        dataPointsArray = contextDataPoints.text;
    } else {
        return false;
    }

    const isValidCitation = dataPointsArray.some(dataPoint => {
        return dataPoint.startsWith(citationCandidate);
    });

    return isValidCitation;
}

export function parseAnswerToHtml(
    answer: ChatAppResponse,
    isStreaming: boolean,
    onCitationClicked: (citationFilePath: string, citationInfo?: CitationResult) => void,
    config?: Config
): HtmlParsedAnswer {
    const contextDataPoints = answer.context.data_points;
    const citations: string[] = [];
    const citationInfos: CitationResult[] = [];

    // Trim any whitespace from the end of the answer after removing follow-up questions
    let parsedAnswer = answer.message.content.trim();

    // Omit a citation that is still being typed during streaming
    if (isStreaming) {
        let lastIndex = parsedAnswer.length;
        for (let i = parsedAnswer.length - 1; i >= 0; i--) {
            if (parsedAnswer[i] === "]") {
                break;
            } else if (parsedAnswer[i] === "[") {
                lastIndex = i;
                break;
            }
        }
        const truncatedAnswer = parsedAnswer.substring(0, lastIndex);
        parsedAnswer = truncatedAnswer;
    }

    const parts = parsedAnswer.split(/\[([^\]]+)\]/g);

    const fragments: string[] = parts.map((part, index) => {
        if (index % 2 === 0) {
            return part;
        } else {
            let citationIndex: number;

            if (!isCitationValid(contextDataPoints, part)) {
                return `[${part}]`;
            }

            let citationInfo: CitationResult | undefined;
            let path: string;

            // Try to use advanced citation strategies if available
            if (config?.citationStrategies) {
                citationInfo = getCitationInfo(part, config);
                path = citationInfo.url;

                // Store citation info for potential use by the caller
                if (citations.indexOf(part) === -1) {
                    citationInfos.push(citationInfo);
                }
            } else {
                // Fall back to legacy citation handling
                path = getCitationFilePath(part, config?.citationBaseUrl);
            }

            if (citations.indexOf(part) !== -1) {
                citationIndex = citations.indexOf(part) + 1;
            } else {
                citations.push(part);
                citationIndex = citations.length;
            }

            return renderToStaticMarkup(
                <a
                    className="supContainer"
                    title={part}
                    onClick={() => onCitationClicked(path, citationInfo)}
                    style={{
                        cursor: "pointer",
                        // Add visual indication if authentication is required
                        ...(citationInfo?.requiresAuth && {
                            borderBottom: "1px dashed #666",
                            position: "relative"
                        })
                    }}
                >
                    <sup>{citationIndex}</sup>
                    {citationInfo?.requiresAuth && (
                        <span
                            title="This citation requires authentication"
                            style={{
                                fontSize: "0.7em",
                                color: "#666",
                                marginLeft: "2px"
                            }}
                        >
                            🔒
                        </span>
                    )}
                </a>
            );
        }
    });

    return {
        answerHtml: fragments.join(""),
        citations,
        citationInfo: citationInfos.length > 0 ? citationInfos : undefined
    };
}
