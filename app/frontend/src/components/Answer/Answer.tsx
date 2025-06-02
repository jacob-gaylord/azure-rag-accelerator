import { useMemo, useState } from "react";
import { Stack, IconButton } from "@fluentui/react";
import { useTranslation } from "react-i18next";
import DOMPurify from "dompurify";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

import styles from "./Answer.module.css";
import { ChatAppResponse, getCitationFilePath, getAdvancedCitationFilePath, getCitationInfo, SpeechConfig, Config, CitationResult } from "../../api";
import { parseAnswerToHtml } from "./AnswerParser";
import { AnswerIcon } from "./AnswerIcon";
import { SpeechOutputBrowser } from "./SpeechOutputBrowser";
import { SpeechOutputAzure } from "./SpeechOutputAzure";
import { FeedbackButtons } from "./FeedbackButtons";

interface Props {
    answer: ChatAppResponse;
    index: number;
    speechConfig: SpeechConfig;
    isSelected?: boolean;
    isStreaming: boolean;
    onCitationClicked: (filePath: string, citationInfo?: CitationResult) => void;
    onThoughtProcessClicked: () => void;
    onSupportingContentClicked: () => void;
    onFollowupQuestionClicked?: (question: string) => void;
    showFollowupQuestions?: boolean;
    showSpeechOutputBrowser?: boolean;
    showSpeechOutputAzure?: boolean;
    messageId?: string;
    sessionId?: string;
    config?: Config;
}

export const Answer = ({
    answer,
    index,
    speechConfig,
    isSelected,
    isStreaming,
    onCitationClicked,
    onThoughtProcessClicked,
    onSupportingContentClicked,
    onFollowupQuestionClicked,
    showFollowupQuestions,
    showSpeechOutputAzure,
    showSpeechOutputBrowser,
    messageId,
    sessionId,
    config
}: Props) => {
    const followupQuestions = answer.context?.followup_questions;
    const parsedAnswer = useMemo(() => parseAnswerToHtml(answer, isStreaming, onCitationClicked, config), [answer, config]);
    const { t } = useTranslation();
    const sanitizedAnswerHtml = DOMPurify.sanitize(parsedAnswer.answerHtml);
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        // Single replace to remove all HTML tags to remove the citations
        const textToCopy = sanitizedAnswerHtml.replace(/<a [^>]*><sup>\d+<\/sup><\/a>|<[^>]+>/g, "");

        navigator.clipboard
            .writeText(textToCopy)
            .then(() => {
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            })
            .catch(err => console.error("Failed to copy text: ", err));
    };

    const handleCitationClick = (citation: string) => {
        // Generate citation info using advanced strategies if available
        if (config?.citationStrategies) {
            const citationInfo = getCitationInfo(citation, config);
            onCitationClicked(citationInfo.url, citationInfo);
        } else {
            // Fall back to legacy citation handling
            const path = getCitationFilePath(citation, config?.citationBaseUrl);
            onCitationClicked(path);
        }
    };

    return (
        <Stack className={`${styles.answerContainer} ${isSelected && styles.selected}`} verticalAlign="space-between">
            <Stack.Item>
                <Stack horizontal horizontalAlign="space-between">
                    <AnswerIcon />
                    <div>
                        <IconButton
                            style={{ color: "black" }}
                            iconProps={{ iconName: copied ? "CheckMark" : "Copy" }}
                            title={copied ? t("tooltips.copied") : t("tooltips.copy")}
                            ariaLabel={copied ? t("tooltips.copied") : t("tooltips.copy")}
                            onClick={handleCopy}
                        />
                        <IconButton
                            style={{ color: "black" }}
                            iconProps={{ iconName: "Lightbulb" }}
                            title={t("tooltips.showThoughtProcess")}
                            ariaLabel={t("tooltips.showThoughtProcess")}
                            onClick={() => onThoughtProcessClicked()}
                            disabled={!answer.context.thoughts?.length || isStreaming}
                        />
                        <IconButton
                            style={{ color: "black" }}
                            iconProps={{ iconName: "ClipboardList" }}
                            title={t("tooltips.showSupportingContent")}
                            ariaLabel={t("tooltips.showSupportingContent")}
                            onClick={() => onSupportingContentClicked()}
                            disabled={!answer.context.data_points || isStreaming}
                        />
                        {showSpeechOutputAzure && (
                            <SpeechOutputAzure answer={sanitizedAnswerHtml} index={index} speechConfig={speechConfig} isStreaming={isStreaming} />
                        )}
                        {showSpeechOutputBrowser && <SpeechOutputBrowser answer={sanitizedAnswerHtml} />}
                    </div>
                </Stack>
            </Stack.Item>

            <Stack.Item grow>
                <div className={styles.answerText}>
                    <ReactMarkdown children={sanitizedAnswerHtml} rehypePlugins={[rehypeRaw]} remarkPlugins={[remarkGfm]} />
                </div>
            </Stack.Item>

            {!!parsedAnswer.citations.length && (
                <Stack.Item>
                    <Stack horizontal wrap tokens={{ childrenGap: 5 }}>
                        <span className={styles.citationLearnMore}>{t("citationWithColon")}</span>
                        {parsedAnswer.citations.map((x, i) => {
                            // Get citation info for display enhancements
                            let citationInfo: CitationResult | undefined;
                            let citationTitle = x;

                            if (config?.citationStrategies) {
                                citationInfo = getCitationInfo(x, config);
                                if (citationInfo.requiresAuth) {
                                    citationTitle = `🔒 ${x}`;
                                }
                                if (citationInfo.error) {
                                    citationTitle = `⚠️ ${x}`;
                                }
                            }

                            return (
                                <a
                                    key={i}
                                    className={styles.citation}
                                    title={`${citationTitle}${citationInfo?.requiresAuth ? " (Authentication required)" : ""}${citationInfo?.error ? ` (Error: ${citationInfo.error})` : ""}`}
                                    onClick={() => handleCitationClick(x)}
                                    style={{
                                        ...(citationInfo?.requiresAuth && {
                                            borderBottom: "1px dashed #666"
                                        }),
                                        ...(citationInfo?.error && {
                                            color: "#d73a49",
                                            borderBottom: "1px dashed #d73a49"
                                        })
                                    }}
                                >
                                    {`${++i}. ${x}`}
                                    {citationInfo?.requiresAuth && <span style={{ marginLeft: "4px", fontSize: "0.8em" }}>🔒</span>}
                                    {citationInfo?.error && <span style={{ marginLeft: "4px", fontSize: "0.8em" }}>⚠️</span>}
                                </a>
                            );
                        })}
                    </Stack>
                </Stack.Item>
            )}

            {/* Show citation strategy info if available for debugging/admin purposes */}
            {parsedAnswer.citationInfo && config?.citationStrategies && (
                <Stack.Item>
                    <div style={{ fontSize: "0.8em", color: "#666", marginTop: "8px" }}>
                        {parsedAnswer.citationInfo.map((info, i) => (
                            <div key={i} style={{ marginBottom: "2px" }}>
                                Strategy: {info.strategyUsed}
                                {info.metadata?.strategyType && ` (${info.metadata.strategyType})`}
                                {info.requiresAuth && " - Auth Required"}
                                {info.error && ` - Error: ${info.error}`}
                            </div>
                        ))}
                    </div>
                </Stack.Item>
            )}

            {!!followupQuestions?.length && showFollowupQuestions && onFollowupQuestionClicked && (
                <Stack.Item>
                    <Stack horizontal wrap className={`${!!parsedAnswer.citations.length ? styles.followupQuestionsList : ""}`} tokens={{ childrenGap: 6 }}>
                        <span className={styles.followupQuestionLearnMore}>{t("followupQuestions")}</span>
                        {followupQuestions.map((x, i) => {
                            return (
                                <a key={i} className={styles.followupQuestion} title={x} onClick={() => onFollowupQuestionClicked(x)}>
                                    {`${x}`}
                                </a>
                            );
                        })}
                    </Stack>
                </Stack.Item>
            )}

            {/* Feedback buttons - only show when messageId and sessionId are available */}
            {messageId && sessionId && (
                <Stack.Item>
                    <FeedbackButtons messageId={messageId} sessionId={sessionId} isStreaming={isStreaming} />
                </Stack.Item>
            )}
        </Stack>
    );
};
