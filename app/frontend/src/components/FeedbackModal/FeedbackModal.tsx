import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import styles from "./FeedbackModal.module.css";

interface FeedbackModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit: (comment: string) => Promise<void>;
    messageId: string;
}

export const FeedbackModal: React.FC<FeedbackModalProps> = ({ isOpen, onClose, onSubmit, messageId }) => {
    const [comment, setComment] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const { t } = useTranslation();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!comment.trim()) return;

        setIsSubmitting(true);
        try {
            await onSubmit(comment);
            setComment("");
            onClose();
        } catch (error) {
            console.error("Failed to submit feedback:", error);
            // TODO: Show error toast/notification
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleOverlayClick = (e: React.MouseEvent) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    if (!isOpen) return null;

    return (
        <div className={styles.feedbackModalOverlay} onClick={handleOverlayClick}>
            <div className={styles.feedbackModal}>
                <h3>{t("feedback.title", "Help us improve")}</h3>
                <p>{t("feedback.description", "What could have been better about this response?")}</p>
                <form onSubmit={handleSubmit}>
                    <textarea
                        value={comment}
                        onChange={e => setComment(e.target.value)}
                        placeholder={t("feedback.placeholder", "Your feedback...")}
                        rows={4}
                        maxLength={500}
                        className={styles.feedbackTextarea}
                        disabled={isSubmitting}
                    />
                    <div className={styles.feedbackModalActions}>
                        <button type="button" onClick={onClose} disabled={isSubmitting} className={styles.cancelButton}>
                            {t("feedback.cancel", "Cancel")}
                        </button>
                        <button type="submit" disabled={!comment.trim() || isSubmitting} className={styles.submitButton}>
                            {isSubmitting ? t("feedback.submitting", "Submitting...") : t("feedback.submit", "Submit")}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
