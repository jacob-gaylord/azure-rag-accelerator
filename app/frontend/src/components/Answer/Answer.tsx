import { useMemo, useState } from "react";
import { Stack, IconButton } from "@fluentui/react";
import { useTranslation } from "react-i18next";
import DOMPurify from "dompurify";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

import styles from "./Answer.module.css";
import { ChatAppResponse, getCitationFilePath, SpeechConfig, submitFeedbackApi, FeedbackRequest } from "../../api";
import { parseAnswerToHtml } from "./AnswerParser";
import { AnswerIcon } from "./AnswerIcon";
import { SpeechOutputBrowser } from "./SpeechOutputBrowser";
import { SpeechOutputAzure } from "./SpeechOutputAzure";
import { FeedbackModal } from "../FeedbackModal";
import { getToken } from "../../authConfig";
import { useMsal } from "@azure/msal-react";

interface FeedbackState {
    type: "positive" | "negative" | null;
    comment?: string;
    timestamp?: string;
}

interface Props {
    answer: ChatAppResponse;
    index: number;
    speechConfig: SpeechConfig;
    isSelected?: boolean;
    isStreaming: boolean;
    onCitationClicked: (filePath: string) => void;
    onThoughtProcessClicked: () => void;
    onSupportingContentClicked: () => void;
    onFollowupQuestionClicked?: (question: string) => void;
    showFollowupQuestions?: boolean;
    showSpeechOutputBrowser?: boolean;
    showSpeechOutputAzure?: boolean;
    conversationId?: string;
    messageId?: string;
    onFeedbackSubmit?: (messageIndex: number, type: "positive" | "negative" | "neutral", comment?: string) => void;
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
    conversationId,
    messageId,
    onFeedbackSubmit
}: Props) => {
    const followupQuestions = answer.context?.followup_questions;
    const parsedAnswer = useMemo(() => parseAnswerToHtml(answer, isStreaming, onCitationClicked), [answer]);
    const { t } = useTranslation();
    const sanitizedAnswerHtml = DOMPurify.sanitize(parsedAnswer.answerHtml);
    const [copied, setCopied] = useState(false);
    const [feedback, setFeedback] = useState<FeedbackState>({ type: null });
    const [showFeedbackModal, setShowFeedbackModal] = useState(false);
    const { instance: client } = useMsal();

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

    const handlePositiveFeedback = async () => {
        try {
            if (feedback.type === "positive") {
                // Remove positive feedback
                if (onFeedbackSubmit) {
                    onFeedbackSubmit(index, "neutral", undefined);
                }
                setFeedback({ type: null });
            } else {
                // Set positive feedback
                if (onFeedbackSubmit) {
                    onFeedbackSubmit(index, "positive", undefined);
                }
                setFeedback({ type: "positive", timestamp: new Date().toISOString() });
            }
        } catch (error) {
            console.error("Failed to submit positive feedback:", error);
        }
    };

    const handleNegativeFeedback = () => {
        if (feedback.type === "negative") {
            // Remove negative feedback
            try {
                if (onFeedbackSubmit) {
                    onFeedbackSubmit(index, "neutral", undefined);
                }
                setFeedback({ type: null });
            } catch (error) {
                console.error("Failed to remove negative feedback:", error);
            }
        } else {
            // Set negative feedback - open modal
            setShowFeedbackModal(true);
        }
    };

    const handleFeedbackModalSubmit = async (comment: string) => {
        try {
            // Use callback for local state management instead of API call
            if (onFeedbackSubmit) {
                onFeedbackSubmit(index, "negative", comment);
            }
            setFeedback({ type: "negative", comment, timestamp: new Date().toISOString() });
        } catch (error) {
            console.error("Failed to submit negative feedback:", error);
            throw error; // Re-throw to let the modal handle the error
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
                        {conversationId && messageId && !isStreaming && (
                            <>
                                <IconButton
                                    style={{
                                        color: feedback.type === "positive" ? "#107c10" : "black",
                                        backgroundColor: feedback.type === "positive" ? "#f3f2f1" : "transparent"
                                    }}
                                    iconProps={{ iconName: "Like" }}
                                    title={
                                        feedback.type === "positive"
                                            ? t("feedback.changeToNeutral", "Remove helpful feedback")
                                            : t("feedback.thumbsUp", "This response was helpful")
                                    }
                                    ariaLabel={
                                        feedback.type === "positive"
                                            ? t("feedback.changeToNeutral", "Remove helpful feedback")
                                            : t("feedback.thumbsUp", "This response was helpful")
                                    }
                                    onClick={handlePositiveFeedback}
                                />
                                <IconButton
                                    style={{
                                        color: feedback.type === "negative" ? "#d13438" : "black",
                                        backgroundColor: feedback.type === "negative" ? "#f3f2f1" : "transparent"
                                    }}
                                    iconProps={{ iconName: "Dislike" }}
                                    title={
                                        feedback.type === "negative"
                                            ? t("feedback.changeToNeutral", "Remove unhelpful feedback")
                                            : t("feedback.thumbsDown", "This response was not helpful")
                                    }
                                    ariaLabel={
                                        feedback.type === "negative"
                                            ? t("feedback.changeToNeutral", "Remove unhelpful feedback")
                                            : t("feedback.thumbsDown", "This response was not helpful")
                                    }
                                    onClick={handleNegativeFeedback}
                                />
                            </>
                        )}
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
                            const path = getCitationFilePath(x);
                            return (
                                <a key={i} className={styles.citation} title={x} onClick={() => onCitationClicked(path)}>
                                    {`${++i}. ${x}`}
                                </a>
                            );
                        })}
                    </Stack>
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

            <FeedbackModal
                isOpen={showFeedbackModal}
                onClose={() => setShowFeedbackModal(false)}
                onSubmit={handleFeedbackModalSubmit}
                messageId={messageId || ""}
            />
        </Stack>
    );
};
