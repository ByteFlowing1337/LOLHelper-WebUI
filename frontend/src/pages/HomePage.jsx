import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Layout,
  Card,
  Space,
  Typography,
  Badge,
  Input,
  Button,
  Row,
  Col,
  Divider,
  message,
  Spin,
  List,
  Tag,
  Avatar,
} from "antd";
import {
  SearchOutlined,
  ThunderboltOutlined,
  SafetyOutlined,
  CheckCircleOutlined,
  BarChartOutlined,
  EyeOutlined,
  LinkOutlined,
  RobotOutlined,
  TrophyOutlined,
  UserOutlined,
} from "@ant-design/icons";
import socketService from "@/services/socket";
import {
  postAutoAccept,
  postAutoAnalyze,
  getLcuStatus,
  getSummonerOverview,
  getMatchHistory,
} from "@/services/api";
import "./HomePage.css";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

function HomePage() {
  const navigate = useNavigate();
  const [summonerName, setSummonerName] = useState("");
  const [lcuStatus, setLcuStatus] = useState({
    connected: false,
    message: "等待连接中...",
  });
  const [realtimeStatus, setRealtimeStatus] = useState("等待指令...");
  const [teammateResults, setTeammateResults] = useState([]);
  const [enemyResults, setEnemyResults] = useState([]);
  const [quickHistory, setQuickHistory] = useState([]);
  const [summonerProfile, setSummonerProfile] = useState(null);
  const [loading, setLoading] = useState({ auto: false, quickFetch: false });

  useEffect(() => {
    const socket = socketService.connect();

    const lcuStatusHandler = (data) => {
      setLcuStatus({
        connected: data.connected,
        message: data.message || (data.connected ? "已连接" : "未连接"),
      });
    };

    const realtimeStatusHandler = (data) => {
      setRealtimeStatus(data.message || data.status || "等待指令...");
    };

    const teammateHandler = (data) => {
      setTeammateResults((prev) => [data, ...prev].slice(0, 20));
    };

    const enemyHandler = (data) => {
      setEnemyResults((prev) => [data, ...prev].slice(0, 20));
    };

    socket.on("lcu_status", lcuStatusHandler);
    socket.on("realtime_status", realtimeStatusHandler);
    socket.on("teammate_analysis", teammateHandler);
    socket.on("enemy_analysis", enemyHandler);

    getLcuStatus()
      .then((data) => {
        if (data) {
          setLcuStatus({
            connected: !!data.connected,
            message: data.message || (data.connected ? "已连接" : "未连接"),
          });
        }
      })
      .catch(() => {
        setLcuStatus({ connected: false, message: "状态获取失败" });
      });

    const intervalId = setInterval(() => {
      getLcuStatus()
        .then((data) => {
          if (data) {
            setLcuStatus({
              connected: !!data.connected,
              message: data.message || (data.connected ? "已连接" : "未连接"),
            });
          }
        })
        .catch(() => {
          setLcuStatus({ connected: false, message: "状态获取失败" });
        });
    }, 5000);

    return () => {
      socket.off("lcu_status", lcuStatusHandler);
      socket.off("realtime_status", realtimeStatusHandler);
      socket.off("teammate_analysis", teammateHandler);
      socket.off("enemy_analysis", enemyHandler);
      socketService.disconnect();
      clearInterval(intervalId);
    };
  }, []);

  const statusBadgeStatus = useMemo(() => {
    if (lcuStatus.connected) return "success";
    return "default";
  }, [lcuStatus.connected]);

  const handleMatchSearch = async () => {
    if (!summonerName.trim()) {
      message.warning("请输入召唤师名称（格式：名称#Tag）");
      return;
    }

    navigate(`/match/${encodeURIComponent(summonerName.trim())}`);
  };

  const handleTftSearch = () => {
    if (!summonerName.trim()) {
      message.warning("请输入召唤师名称（格式：名称#Tag）");
      return;
    }

    navigate(`/tft/${encodeURIComponent(summonerName.trim())}`);
  };

  const handleQuickFetch = async () => {
    if (!summonerName.trim()) {
      message.warning("请输入召唤师名称");
      return;
    }

    setLoading((prev) => ({ ...prev, quickFetch: true }));

    try {
      const [overview, history] = await Promise.all([
        getSummonerOverview(summonerName.trim()),
        getMatchHistory(summonerName.trim(), { count: 5 }),
      ]);

      if (!overview.success) {
        throw new Error(overview.error || "获取召唤师信息失败");
      }

      if (!history.success) {
        throw new Error(history.error || "获取战绩失败");
      }

      // 设置召唤师资料
      const profileData = overview.data || {};
      const ranked = profileData.ranked || {};
      const soloQueue =
        ranked.queues?.find((q) => q.queueType === "RANKED_SOLO_5x5") || {};

      setSummonerProfile({
        name: profileData.name || summonerName.trim(),
        level: profileData.level || 0,
        profileIconId: profileData.profileIconId || 1,
        tier: soloQueue.tier || "UNRANKED",
        rank: soloQueue.rank || "",
        leaguePoints: soloQueue.leaguePoints || 0,
        wins: soloQueue.wins || 0,
        losses: soloQueue.losses || 0,
      });

      const matches = history.matches?.map((item) => ({
        gameId: item.gameId,
        champion: item.championName || item.championId,
        kills: item.kills,
        deaths: item.deaths,
        assists: item.assists,
        win: item.result === "Win" || item.win,
        gameMode: item.gameMode || item.queue,
        duration: item.gameDuration,
        timeAgo: item.timeAgo,
      }));

      setQuickHistory(matches || []);
      message.success("快速战绩获取成功");
    } catch (error) {
      message.error(error.message || "快速战绩获取失败");
    } finally {
      setLoading((prev) => ({ ...prev, quickFetch: false }));
    }
  };

  const handleAutoAccept = async () => {
    setLoading((prev) => ({ ...prev, auto: true }));
    try {
      const result = await postAutoAccept();
      if (result.success) {
        message.success(result.message || "自动接受已启用");
        setRealtimeStatus("自动接受对局已启用");
      } else {
        message.error(result.error || "自动接受失败");
      }
    } catch (error) {
      message.error(error.response?.data?.error || "自动接受失败");
    } finally {
      setLoading((prev) => ({ ...prev, auto: false }));
    }
  };

  const handleAutoAnalyze = async () => {
    setLoading((prev) => ({ ...prev, auto: true }));
    try {
      const result = await postAutoAnalyze();
      if (result.success) {
        message.success(result.message || "敌我分析已启用");
        setRealtimeStatus("敌我分析已启用，等待对局开始...");
      } else {
        message.error(result.error || "敌我分析失败");
      }
    } catch (error) {
      message.error(error.response?.data?.error || "敌我分析失败");
    } finally {
      setLoading((prev) => ({ ...prev, auto: false }));
    }
  };

  const handleLiveNavigate = () => {
    navigate("/live");
  };

  return (
    <Layout className="home-layout">
      <Header className="home-header">
        <div className="home-header-inner">
          <div>
            <Title level={3} style={{ margin: 0 }}>
              LCU-UI
            </Title>
            <Text type="secondary">React + Ant Design 现代化界面</Text>
          </div>
        </div>
      </Header>

      <Content className="home-content">
        <div className="home-container">
          <Card className="status-card" bordered={false}>
            <Space size="large" align="center">
              <LinkOutlined style={{ fontSize: 24, color: "#667eea" }} />
              <Text strong>LCU 连接状态：</Text>
              <Badge status={statusBadgeStatus} text={lcuStatus.message} />
            </Space>
          </Card>

          <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
            <Col xs={24} lg={14}>
              <Card
                className="query-card card-gradient-primary"
                title={
                  <Space>
                    <SearchOutlined />
                    <span>战绩查询</span>
                  </Space>
                }
                bordered={false}
              >
                <Space
                  direction="vertical"
                  size="large"
                  style={{ width: "100%" }}
                >
                  <div>
                    <Text strong>召唤师名称</Text>
                    <Input
                      size="large"
                      placeholder="输入召唤师名称（格式：名称#Tag）"
                      prefix={<SearchOutlined />}
                      value={summonerName}
                      onChange={(event) => setSummonerName(event.target.value)}
                      onPressEnter={handleMatchSearch}
                    />
                  </div>

                  <Space direction="vertical" style={{ width: "100%" }}>
                    <Button
                      type="primary"
                      icon={<ThunderboltOutlined />}
                      size="large"
                      block
                      onClick={handleMatchSearch}
                    >
                      查看战绩详情
                    </Button>
                    <Button
                      icon={<SafetyOutlined />}
                      size="large"
                      block
                      onClick={handleTftSearch}
                    >
                      查看 TFT 战绩
                    </Button>
                    <Button
                      icon={<SearchOutlined />}
                      size="large"
                      block
                      loading={loading.quickFetch}
                      onClick={handleQuickFetch}
                    >
                      快速预览最近战绩
                    </Button>
                  </Space>

                  <Divider plain>快速预览</Divider>

                  <Spin spinning={loading.quickFetch}>
                    {summonerProfile && (
                      <div className="summoner-profile">
                        <Avatar
                          size={80}
                          src={`https://ddragon.leagueoflegends.com/cdn/15.1.1/img/profileicon/${summonerProfile.profileIconId}.png`}
                          icon={<UserOutlined />}
                          className="summoner-avatar"
                        />
                        <div className="summoner-info">
                          <div className="summoner-name">
                            {summonerProfile.name}
                          </div>
                          <Space size="small" wrap>
                            <span className="summoner-level">
                              等级 {summonerProfile.level}
                            </span>
                            {summonerProfile.tier !== "UNRANKED" && (
                              <span className="summoner-rank">
                                <TrophyOutlined />
                                {summonerProfile.tier} {summonerProfile.rank} -{" "}
                                {summonerProfile.leaguePoints} LP
                              </span>
                            )}
                          </Space>
                          {summonerProfile.tier !== "UNRANKED" && (
                            <div style={{ marginTop: 8 }}>
                              <Text type="secondary">
                                胜率：{summonerProfile.wins}胜{" "}
                                {summonerProfile.losses}负 (
                                {(
                                  (summonerProfile.wins /
                                    (summonerProfile.wins +
                                      summonerProfile.losses)) *
                                  100
                                ).toFixed(1)}
                                %)
                              </Text>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {quickHistory.length > 0 ? (
                      <List
                        itemLayout="horizontal"
                        dataSource={quickHistory}
                        renderItem={(item) => (
                          <List.Item
                            className={`match-history-item ${
                              item.win ? "win" : "lose"
                            }`}
                            actions={[
                              <Tag color={item.win ? "success" : "error"}>
                                {item.win ? "胜利" : "失败"}
                              </Tag>,
                            ]}
                          >
                            <List.Item.Meta
                              avatar={
                                <Avatar
                                  size={48}
                                  src={`https://ddragon.leagueoflegends.com/cdn/15.1.1/img/champion/${item.champion}.png`}
                                  className="match-champion-icon"
                                />
                              }
                              title={
                                <Space>
                                  <Text strong>{item.champion}</Text>
                                  <Text
                                    type="secondary"
                                    style={{ fontSize: 12 }}
                                  >
                                    {item.timeAgo}
                                  </Text>
                                </Space>
                              }
                              description={
                                <Space split="|">
                                  <Text>
                                    <Text strong>{item.kills}</Text>/
                                    <Text strong style={{ color: "#ef4444" }}>
                                      {item.deaths}
                                    </Text>
                                    /<Text strong>{item.assists}</Text>
                                  </Text>
                                  <Text type="secondary">{item.gameMode}</Text>
                                </Space>
                              }
                            />
                          </List.Item>
                        )}
                      />
                    ) : (
                      !summonerProfile && (
                        <Text type="secondary">
                          使用快速预览可显示最近 5 场对局简报。
                        </Text>
                      )
                    )}
                  </Spin>
                </Space>
              </Card>
            </Col>

            <Col xs={24} lg={10}>
              <Card
                className="automation-card card-gradient-success"
                title={
                  <Space>
                    <RobotOutlined />
                    <span>自动化功能</span>
                  </Space>
                }
                bordered={false}
              >
                <Space
                  direction="vertical"
                  size="large"
                  style={{ width: "100%" }}
                >
                  <Row gutter={[12, 12]}>
                    <Col span={12}>
                      <Button
                        type="primary"
                        icon={<CheckCircleOutlined />}
                        block
                        size="large"
                        loading={loading.auto}
                        onClick={handleAutoAccept}
                      >
                        自动接受对局
                      </Button>
                    </Col>
                    <Col span={12}>
                      <Button
                        type="primary"
                        icon={<BarChartOutlined />}
                        block
                        size="large"
                        loading={loading.auto}
                        onClick={handleAutoAnalyze}
                      >
                        启用敌我分析
                      </Button>
                    </Col>
                  </Row>

                  <Button
                    icon={<EyeOutlined />}
                    block
                    size="large"
                    onClick={handleLiveNavigate}
                  >
                    查看实时游戏
                  </Button>

                  <div className="status-display">
                    <Text strong>实时状态</Text>
                    <Badge status="processing" text={realtimeStatus} />
                  </div>

                  <Divider plain>最新分析</Divider>

                  <Space
                    direction="vertical"
                    size="large"
                    style={{ width: "100%" }}
                  >
                    <Card
                      title="队友分析"
                      size="small"
                      className="results-card"
                    >
                      {teammateResults.length > 0 ? (
                        <List
                          dataSource={teammateResults}
                          renderItem={(item, index) => (
                            <List.Item>
                              <Text code>{index + 1}</Text>
                              <Text style={{ marginLeft: 8 }}>
                                {JSON.stringify(item)}
                              </Text>
                            </List.Item>
                          )}
                        />
                      ) : (
                        <Text type="secondary">等待队友数据分析结果...</Text>
                      )}
                    </Card>

                    <Card
                      title="敌方分析"
                      size="small"
                      className="results-card"
                    >
                      {enemyResults.length > 0 ? (
                        <List
                          dataSource={enemyResults}
                          renderItem={(item, index) => (
                            <List.Item>
                              <Text code>{index + 1}</Text>
                              <Text style={{ marginLeft: 8 }}>
                                {JSON.stringify(item)}
                              </Text>
                            </List.Item>
                          )}
                        />
                      ) : (
                        <Text type="secondary">等待敌方数据分析结果...</Text>
                      )}
                    </Card>
                  </Space>
                </Space>
              </Card>
            </Col>
          </Row>
        </div>
      </Content>
    </Layout>
  );
}

export default HomePage;
