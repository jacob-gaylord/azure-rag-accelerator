import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import {
    Text,
    Pivot,
    PivotItem,
    Stack,
    Separator,
    DefaultButton,
    PrimaryButton,
    Spinner,
    SpinnerSize,
    MessageBar,
    MessageBarType,
    DetailsList,
    DetailsListLayoutMode,
    IColumn,
    SelectionMode,
    SearchBox,
    Dropdown,
    IDropdownOption,
    DatePicker,
    CommandBar,
    ICommandBarItemProps,
    Dialog,
    DialogType,
    DialogFooter
} from "@fluentui/react";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement, ArcElement } from "chart.js";
import { Line, Bar, Doughnut } from "react-chartjs-2";
import { useLogin, getToken } from "../../authConfig";
import { getAdminAnalyticsApi, getAdminFeedbackApi, getAdminChatHistoryApi, exportDataApi } from "../../api/api";
import { useMsal } from "@azure/msal-react";
import styles from "./AdminDashboard.module.css";

// Register Chart.js components
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, BarElement, ArcElement);

interface AdminAnalytics {
    totalFeedback: number;
    averageRating: number;
    totalSessions: number;
    totalMessages: number;
    feedbackTrends: Array<{ date: string; count: number; avgRating: number }>;
    ratingDistribution: Array<{ rating: number; count: number }>;
    topIssues: Array<{ issue: string; count: number }>;
    sessionMetrics: {
        avgSessionLength: number;
        avgMessagesPerSession: number;
        bounceRate: number;
    };
}

interface FeedbackData {
    id: string;
    messageId: string;
    sessionId: string;
    userId: string;
    rating: number;
    comment?: string;
    timestamp: string;
    messageContent?: string;
}

interface ChatHistoryData {
    id: string;
    sessionId: string;
    userId: string;
    timestamp: string;
    messageCount: number;
    lastMessage: string;
    duration: number;
}

const AdminDashboard: React.FC = () => {
    const { t } = useTranslation();
    const client = useLogin ? useMsal().instance : undefined;
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null);
    const [feedbackData, setFeedbackData] = useState<FeedbackData[]>([]);
    const [chatHistoryData, setChatHistoryData] = useState<ChatHistoryData[]>([]);
    const [filteredFeedback, setFilteredFeedback] = useState<FeedbackData[]>([]);
    const [filteredChatHistory, setFilteredChatHistory] = useState<ChatHistoryData[]>([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [ratingFilter, setRatingFilter] = useState<string>("all");
    const [dateFilter, setDateFilter] = useState<Date | undefined>(undefined);
    const [exportDialogVisible, setExportDialogVisible] = useState(false);
    const [exportFormat, setExportFormat] = useState("csv");
    const [exportType, setExportType] = useState("feedback");

    useEffect(() => {
        loadDashboardData();
    }, []);

    useEffect(() => {
        applyFilters();
    }, [feedbackData, chatHistoryData, searchQuery, ratingFilter, dateFilter]);

    const loadDashboardData = async () => {
        try {
            setLoading(true);
            setError(null);

            const token = useLogin ? await getToken(client!) : undefined;

            const [analyticsResponse, feedbackResponse, chatHistoryResponse] = await Promise.all([
                getAdminAnalyticsApi(token),
                getAdminFeedbackApi(token),
                getAdminChatHistoryApi(token)
            ]);

            setAnalytics(analyticsResponse);
            setFeedbackData(feedbackResponse);
            setChatHistoryData(chatHistoryResponse);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load dashboard data");
        } finally {
            setLoading(false);
        }
    };

    const applyFilters = () => {
        let filtered = feedbackData;

        // Apply search filter
        if (searchQuery) {
            filtered = filtered.filter(
                item =>
                    item.messageId.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    item.sessionId.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    item.userId.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    (item.comment && item.comment.toLowerCase().includes(searchQuery.toLowerCase()))
            );
        }

        // Apply rating filter
        if (ratingFilter !== "all") {
            const rating = parseInt(ratingFilter);
            filtered = filtered.filter(item => item.rating === rating);
        }

        // Apply date filter
        if (dateFilter) {
            const filterDate = dateFilter.toISOString().split("T")[0];
            filtered = filtered.filter(item => item.timestamp.startsWith(filterDate));
        }

        setFilteredFeedback(filtered);

        // Apply similar filters to chat history
        let filteredChat = chatHistoryData;
        if (searchQuery) {
            filteredChat = filteredChat.filter(
                item =>
                    item.sessionId.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    item.userId.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    item.lastMessage.toLowerCase().includes(searchQuery.toLowerCase())
            );
        }

        if (dateFilter) {
            const filterDate = dateFilter.toISOString().split("T")[0];
            filteredChat = filteredChat.filter(item => item.timestamp.startsWith(filterDate));
        }

        setFilteredChatHistory(filteredChat);
    };

    const handleExportData = async () => {
        try {
            const token = useLogin ? await getToken(client!) : undefined;
            const data = exportType === "feedback" ? filteredFeedback : filteredChatHistory;

            await exportDataApi(exportType, exportFormat, data, token);
            setExportDialogVisible(false);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Failed to export data");
        }
    };

    const ratingOptions: IDropdownOption[] = [
        { key: "all", text: t("admin.filters.allRatings") },
        { key: "1", text: "1 Star" },
        { key: "2", text: "2 Stars" },
        { key: "3", text: "3 Stars" },
        { key: "4", text: "4 Stars" },
        { key: "5", text: "5 Stars" }
    ];

    const feedbackColumns: IColumn[] = [
        {
            key: "timestamp",
            name: t("admin.columns.timestamp"),
            fieldName: "timestamp",
            minWidth: 120,
            maxWidth: 150,
            isResizable: true,
            onRender: (item: FeedbackData) => new Date(item.timestamp).toLocaleString()
        },
        {
            key: "rating",
            name: t("admin.columns.rating"),
            fieldName: "rating",
            minWidth: 80,
            maxWidth: 100,
            isResizable: true,
            onRender: (item: FeedbackData) => `${item.rating} ⭐`
        },
        {
            key: "userId",
            name: t("admin.columns.user"),
            fieldName: "userId",
            minWidth: 120,
            maxWidth: 150,
            isResizable: true
        },
        {
            key: "sessionId",
            name: t("admin.columns.session"),
            fieldName: "sessionId",
            minWidth: 120,
            maxWidth: 150,
            isResizable: true
        },
        {
            key: "comment",
            name: t("admin.columns.comment"),
            fieldName: "comment",
            minWidth: 200,
            isResizable: true,
            onRender: (item: FeedbackData) => item.comment || t("admin.noComment")
        }
    ];

    const chatHistoryColumns: IColumn[] = [
        {
            key: "timestamp",
            name: t("admin.columns.timestamp"),
            fieldName: "timestamp",
            minWidth: 120,
            maxWidth: 150,
            isResizable: true,
            onRender: (item: ChatHistoryData) => new Date(item.timestamp).toLocaleString()
        },
        {
            key: "userId",
            name: t("admin.columns.user"),
            fieldName: "userId",
            minWidth: 120,
            maxWidth: 150,
            isResizable: true
        },
        {
            key: "sessionId",
            name: t("admin.columns.session"),
            fieldName: "sessionId",
            minWidth: 120,
            maxWidth: 150,
            isResizable: true
        },
        {
            key: "messageCount",
            name: t("admin.columns.messages"),
            fieldName: "messageCount",
            minWidth: 80,
            maxWidth: 100,
            isResizable: true
        },
        {
            key: "duration",
            name: t("admin.columns.duration"),
            fieldName: "duration",
            minWidth: 100,
            maxWidth: 120,
            isResizable: true,
            onRender: (item: ChatHistoryData) => `${Math.round(item.duration / 60)}m`
        },
        {
            key: "lastMessage",
            name: t("admin.columns.lastMessage"),
            fieldName: "lastMessage",
            minWidth: 200,
            isResizable: true,
            onRender: (item: ChatHistoryData) => item.lastMessage.substring(0, 100) + "..."
        }
    ];

    const commandBarItems: ICommandBarItemProps[] = [
        {
            key: "refresh",
            text: t("admin.actions.refresh"),
            iconProps: { iconName: "Refresh" },
            onClick: loadDashboardData
        },
        {
            key: "export",
            text: t("admin.actions.export"),
            iconProps: { iconName: "Download" },
            onClick: () => setExportDialogVisible(true)
        }
    ];

    if (loading) {
        return (
            <div className={styles.loadingContainer}>
                <Spinner size={SpinnerSize.large} label={t("admin.loading")} />
            </div>
        );
    }

    if (error) {
        return (
            <div className={styles.errorContainer}>
                <MessageBar messageBarType={MessageBarType.error}>{error}</MessageBar>
                <DefaultButton onClick={loadDashboardData} text={t("admin.actions.retry")} />
            </div>
        );
    }

    // Chart data preparation
    const feedbackTrendData = {
        labels: analytics?.feedbackTrends.map(trend => trend.date) || [],
        datasets: [
            {
                label: t("admin.charts.feedbackCount"),
                data: analytics?.feedbackTrends.map(trend => trend.count) || [],
                borderColor: "rgb(75, 192, 192)",
                backgroundColor: "rgba(75, 192, 192, 0.2)",
                yAxisID: "y"
            },
            {
                label: t("admin.charts.avgRating"),
                data: analytics?.feedbackTrends.map(trend => trend.avgRating) || [],
                borderColor: "rgb(255, 99, 132)",
                backgroundColor: "rgba(255, 99, 132, 0.2)",
                yAxisID: "y1"
            }
        ]
    };

    const ratingDistributionData = {
        labels: ["1 Star", "2 Stars", "3 Stars", "4 Stars", "5 Stars"],
        datasets: [
            {
                data: analytics?.ratingDistribution.map(rating => rating.count) || [],
                backgroundColor: ["#FF6384", "#FF9F40", "#FFCD56", "#4BC0C0", "#36A2EB"]
            }
        ]
    };

    return (
        <div className={styles.adminDashboard}>
            <Stack tokens={{ childrenGap: 20 }}>
                <Text variant="xxLarge" className={styles.title}>
                    {t("admin.title")}
                </Text>

                <CommandBar items={commandBarItems} />

                {/* Key Metrics Cards */}
                <Stack horizontal tokens={{ childrenGap: 16 }} wrap>
                    <div className={styles.metricCard}>
                        <Stack>
                            <Text variant="large">{analytics?.totalFeedback || 0}</Text>
                            <Text variant="medium">{t("admin.metrics.totalFeedback")}</Text>
                        </Stack>
                    </div>
                    <div className={styles.metricCard}>
                        <Stack>
                            <Text variant="large">{analytics?.averageRating.toFixed(1) || "0.0"}</Text>
                            <Text variant="medium">{t("admin.metrics.avgRating")}</Text>
                        </Stack>
                    </div>
                    <div className={styles.metricCard}>
                        <Stack>
                            <Text variant="large">{analytics?.totalSessions || 0}</Text>
                            <Text variant="medium">{t("admin.metrics.totalSessions")}</Text>
                        </Stack>
                    </div>
                    <div className={styles.metricCard}>
                        <Stack>
                            <Text variant="large">{analytics?.totalMessages || 0}</Text>
                            <Text variant="medium">{t("admin.metrics.totalMessages")}</Text>
                        </Stack>
                    </div>
                </Stack>

                <Pivot>
                    <PivotItem headerText={t("admin.tabs.analytics")}>
                        <Stack tokens={{ childrenGap: 20 }}>
                            <Stack horizontal tokens={{ childrenGap: 20 }} wrap>
                                <div className={styles.chartCard}>
                                    <Text variant="large">{t("admin.charts.feedbackTrends")}</Text>
                                    <Line
                                        data={feedbackTrendData}
                                        options={{
                                            responsive: true,
                                            scales: {
                                                y: { type: "linear", display: true, position: "left" },
                                                y1: { type: "linear", display: true, position: "right", grid: { drawOnChartArea: false } }
                                            }
                                        }}
                                    />
                                </div>
                                <div className={styles.chartCard}>
                                    <Text variant="large">{t("admin.charts.ratingDistribution")}</Text>
                                    <Doughnut data={ratingDistributionData} options={{ responsive: true }} />
                                </div>
                            </Stack>
                        </Stack>
                    </PivotItem>

                    <PivotItem headerText={t("admin.tabs.feedback")}>
                        <Stack tokens={{ childrenGap: 16 }}>
                            {/* Filters */}
                            <Stack horizontal tokens={{ childrenGap: 16 }} wrap>
                                <SearchBox
                                    placeholder={t("admin.filters.searchPlaceholder")}
                                    value={searchQuery}
                                    onChange={(_, newValue) => setSearchQuery(newValue || "")}
                                />
                                <Dropdown
                                    placeholder={t("admin.filters.ratingPlaceholder")}
                                    options={ratingOptions}
                                    selectedKey={ratingFilter}
                                    onChange={(_, option) => setRatingFilter((option?.key as string) || "all")}
                                />
                                <DatePicker
                                    placeholder={t("admin.filters.datePlaceholder")}
                                    value={dateFilter}
                                    onSelectDate={date => setDateFilter(date || undefined)}
                                />
                            </Stack>

                            <DetailsList
                                items={filteredFeedback}
                                columns={feedbackColumns}
                                layoutMode={DetailsListLayoutMode.justified}
                                selectionMode={SelectionMode.none}
                                className={styles.detailsList}
                            />
                        </Stack>
                    </PivotItem>

                    <PivotItem headerText={t("admin.tabs.chatHistory")}>
                        <Stack tokens={{ childrenGap: 16 }}>
                            {/* Filters */}
                            <Stack horizontal tokens={{ childrenGap: 16 }} wrap>
                                <SearchBox
                                    placeholder={t("admin.filters.searchChatPlaceholder")}
                                    value={searchQuery}
                                    onChange={(_, newValue) => setSearchQuery(newValue || "")}
                                />
                                <DatePicker
                                    placeholder={t("admin.filters.datePlaceholder")}
                                    value={dateFilter}
                                    onSelectDate={date => setDateFilter(date || undefined)}
                                />
                            </Stack>

                            <DetailsList
                                items={filteredChatHistory}
                                columns={chatHistoryColumns}
                                layoutMode={DetailsListLayoutMode.justified}
                                selectionMode={SelectionMode.none}
                                className={styles.detailsList}
                            />
                        </Stack>
                    </PivotItem>
                </Pivot>

                {/* Export Dialog */}
                <Dialog
                    hidden={!exportDialogVisible}
                    onDismiss={() => setExportDialogVisible(false)}
                    dialogContentProps={{
                        type: DialogType.normal,
                        title: t("admin.export.title"),
                        subText: t("admin.export.description")
                    }}
                >
                    <Stack tokens={{ childrenGap: 16 }}>
                        <Dropdown
                            label={t("admin.export.type")}
                            options={[
                                { key: "feedback", text: t("admin.export.feedback") },
                                { key: "chatHistory", text: t("admin.export.chatHistory") }
                            ]}
                            selectedKey={exportType}
                            onChange={(_, option) => setExportType((option?.key as string) || "feedback")}
                        />
                        <Dropdown
                            label={t("admin.export.format")}
                            options={[
                                { key: "csv", text: "CSV" },
                                { key: "json", text: "JSON" }
                            ]}
                            selectedKey={exportFormat}
                            onChange={(_, option) => setExportFormat((option?.key as string) || "csv")}
                        />
                    </Stack>
                    <DialogFooter>
                        <PrimaryButton onClick={handleExportData} text={t("admin.export.download")} />
                        <DefaultButton onClick={() => setExportDialogVisible(false)} text={t("admin.export.cancel")} />
                    </DialogFooter>
                </Dialog>
            </Stack>
        </div>
    );
};

export default AdminDashboard;

// For lazy loading compatibility
export { AdminDashboard as Component };
