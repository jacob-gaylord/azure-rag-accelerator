import { useState, useEffect } from "react";
import { Stack, IconButton, Rating, TextField, PrimaryButton, DefaultButton, Spinner } from "@fluentui/react";
import { useTranslation } from "react-i18next";
import { useMsal } from "@azure/msal-react";
import { submitFeedbackApi, getFeedbackByMessageApi, updateFeedbackApi, FeedbackData } from "../../api";
import { getToken } from "../../authConfig";

import styles from "./FeedbackButtons.module.css";

interface Props {
    messageId: string;
    sessionId: string;
    isStreaming: boolean;
}

export const FeedbackButtons = ({ messageId, sessionId, isStreaming }: Props) => {
    const { t } = useTranslation();
    const { instance, accounts } = useMsal();

    const [rating, setRating] = useState<number>(0);
    const [comment, setComment] = useState<string>("");
    const [showCommentBox, setShowCommentBox] = useState<boolean>(false);
    const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
    const [existingFeedback, setExistingFeedback] = useState<FeedbackData | null>(null);
    const [showConfirmation, setShowConfirmation] = useState<boolean>(false);
    const [error, setError] = useState<string>("");

    // Load existing feedback on component mount
    useEffect(() => {
        loadExistingFeedback();
    }, [messageId]);

    const loadExistingFeedback = async () => {
        try {
            const token = await getToken(instance);
            if (!token) {
                console.log("No token available for loading feedback");
                return;
            }
            const response = await getFeedbackByMessageApi(messageId, token);

            if (response.feedback && response.feedback.length > 0) {
                const feedback = response.feedback[0];
                setExistingFeedback(feedback);
                setRating(feedback.rating);
                if (feedback.comment) {
                    setComment(feedback.comment);
                    setShowCommentBox(true);
                }
            }
        } catch (error) {
            console.log("No existing feedback found or error loading feedback:", error);
        }
    };

    const handleRatingChange = (event: React.FormEvent<HTMLElement>, rating?: number) => {
        if (rating !== undefined) {
            setRating(rating);
            setError("");

            // Show comment box for ratings <= 3 or if user clicks rating again when already set
            if (rating <= 3 || showCommentBox) {
                setShowCommentBox(true);
            }
        }
    };

    const handleThumbsUp = () => {
        const newRating = rating === 5 ? 0 : 5;
        setRating(newRating);
        setError("");

        if (newRating === 0) {
            setShowCommentBox(false);
            setComment("");
        }
    };

    const handleThumbsDown = () => {
        const newRating = rating === 1 ? 0 : 1;
        setRating(newRating);
        setError("");

        if (newRating === 1) {
            setShowCommentBox(true);
        } else {
            setShowCommentBox(false);
            setComment("");
        }
    };

    const handleSubmit = async () => {
        if (rating === 0) {
            setError(t("feedback.pleaseSelectRating"));
            return;
        }

        if (comment.length > 1000) {
            setError(t("feedback.commentTooLong"));
            return;
        }

        setIsSubmitting(true);
        setError("");

        try {
            const token = await getToken(instance);

            if (existingFeedback) {
                // Update existing feedback
                await updateFeedbackApi(existingFeedback.id, { rating, comment }, token || "");
            } else {
                // Submit new feedback
                await submitFeedbackApi({ sessionId, messageId, rating, comment }, token || "");
            }

            setShowConfirmation(true);
            setTimeout(() => setShowConfirmation(false), 3000);

            // Reload feedback to get the latest data
            await loadExistingFeedback();
        } catch (error) {
            setError(t("feedback.submitError"));
            console.error("Error submitting feedback:", error);
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleCancel = () => {
        if (existingFeedback) {
            setRating(existingFeedback.rating);
            setComment(existingFeedback.comment || "");
            setShowCommentBox(!!existingFeedback.comment);
        } else {
            setRating(0);
            setComment("");
            setShowCommentBox(false);
        }
        setError("");
    };

    const hasChanges = existingFeedback ? rating !== existingFeedback.rating || comment !== (existingFeedback.comment || "") : rating > 0 || comment.length > 0;

    if (isStreaming) {
        return null; // Hide feedback buttons while response is streaming
    }

    return (
        <div className={styles.feedbackContainer}>
            <div className={styles.feedbackButtons}>
                {/* Quick thumbs up/down buttons */}
                <IconButton
                    className={`${styles.thumbButton} ${rating === 5 ? styles.thumbSelected : ""}`}
                    iconProps={{ iconName: "Like" }}
                    title={t("feedback.thumbsUp")}
                    ariaLabel={t("feedback.thumbsUp")}
                    onClick={handleThumbsUp}
                />
                <IconButton
                    className={`${styles.thumbButton} ${rating === 1 ? styles.thumbSelected : ""}`}
                    iconProps={{ iconName: "Dislike" }}
                    title={t("feedback.thumbsDown")}
                    ariaLabel={t("feedback.thumbsDown")}
                    onClick={handleThumbsDown}
                />

                {/* 5-star rating component */}
                <Rating
                    rating={rating}
                    onChange={handleRatingChange}
                    allowZeroStars={true}
                    max={5}
                    className={styles.starRating}
                    ariaLabel={t("feedback.starRating")}
                />
            </div>

            {/* Expandable comment section */}
            {showCommentBox && (
                <div className={styles.commentSection}>
                    <TextField
                        value={comment}
                        onChange={(_, newValue) => setComment(newValue || "")}
                        placeholder={t("feedback.commentPlaceholder")}
                        multiline
                        rows={3}
                        maxLength={1000}
                        className={styles.commentField}
                        ariaLabel={t("feedback.commentLabel")}
                    />
                    <div className={styles.commentActions}>
                        <span className={styles.characterCount}>{comment.length}/1000</span>
                        <Stack horizontal tokens={{ childrenGap: 8 }}>
                            <DefaultButton text={t("feedback.cancel")} onClick={handleCancel} disabled={isSubmitting} />
                            <PrimaryButton
                                text={isSubmitting ? t("feedback.submitting") : t("feedback.submit")}
                                onClick={handleSubmit}
                                disabled={isSubmitting || !hasChanges}
                            >
                                {isSubmitting && <Spinner size={1} />}
                            </PrimaryButton>
                        </Stack>
                    </div>
                </div>
            )}

            {/* Action buttons for when no comment box is shown */}
            {!showCommentBox && rating > 0 && (
                <div className={styles.quickActions}>
                    <DefaultButton
                        text={t("feedback.addComment")}
                        onClick={() => setShowCommentBox(true)}
                        disabled={isSubmitting}
                        iconProps={{ iconName: "Comment" }}
                    />
                    <PrimaryButton
                        text={isSubmitting ? t("feedback.submitting") : t("feedback.submit")}
                        onClick={handleSubmit}
                        disabled={isSubmitting || !hasChanges}
                    >
                        {isSubmitting && <Spinner size={1} />}
                    </PrimaryButton>
                </div>
            )}

            {/* Status messages */}
            {error && (
                <div className={styles.errorMessage} role="alert">
                    {error}
                </div>
            )}

            {showConfirmation && (
                <div className={styles.successMessage} role="status">
                    {t("feedback.submitSuccess")}
                </div>
            )}
        </div>
    );
};
