import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Layout,
  Button,
  Typography,
  Card,
  List,
  Tag,
  Row,
  Col,
  Statistic,
  Table,
  Space,
  message,
  Spin,
  Avatar,
} from "antd";
import {
  ArrowLeftOutlined,
  TrophyOutlined,
  FireOutlined,
  ClockCircleOutlined,
  UserOutlined,
} from "@ant-design/icons";
import {
  getMatchHistory,
  getMatchDetail,
  getSummonerOverview,
} from "@/services/api";
import "./MatchDetailPage.css";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const columns = [
  {
    title: "召唤师",
    dataIndex: "summonerName",
    key: "summonerName",
    render: (text, record) => (
      <Space direction="vertical" size={0}>
        <Text strong>{text}</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {record.championName}
        </Text>
      </Space>
    ),
  },
  {
    title: "K/D/A",
    key: "kda",
    render: (_, record) => (
      <Space direction="vertical" size={0}>
        <Text
          strong
        >{`${record.kills}/${record.deaths}/${record.assists}`}</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          KDA:{" "}
          {record.deaths > 0
            ? ((record.kills + record.assists) / record.deaths).toFixed(2)
            : record.kills + record.assists}
        </Text>
      </Space>
    ),
  },
  {
    title: "伤害",
    dataIndex: "totalDamageDealtToChampions",
    key: "totalDamageDealtToChampions",
    render: (value) => value?.toLocaleString() || 0,
  },
  {
    title: "承伤",
    dataIndex: "totalDamageTaken",
    key: "totalDamageTaken",
    render: (value) => value?.toLocaleString() || 0,
  },
  {
    title: "金钱",
    dataIndex: "goldEarned",
    key: "goldEarned",
    render: (value) => value?.toLocaleString() || 0,
  },
  {
    title: "补刀",
    dataIndex: "totalMinionsKilled",
    key: "totalMinionsKilled",
  },
  {
    title: "视野分",
    dataIndex: "visionScore",
    key: "visionScore",
  },
];

function groupParticipants(participants) {
  const blue = participants.filter((item) => item.teamId === 100);
  const red = participants.filter((item) => item.teamId === 200);
  return { blue, red };
}

function MatchDetailPage() {
  const { summonerName } = useParams();
  const navigate = useNavigate();
  const [history, setHistory] = useState([]);
  const [selectedMatch, setSelectedMatch] = useState(null);
  const [summonerProfile, setSummonerProfile] = useState(null);
  const [loading, setLoading] = useState(false);
  const decodedName = decodeURIComponent(summonerName || "");

  useEffect(() => {
    if (!decodedName) {
      navigate("/");
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        const [historyResult, overviewResult] = await Promise.all([
          getMatchHistory(decodedName, { count: 10 }),
          getSummonerOverview(decodedName),
        ]);

        if (!historyResult.success) {
          throw new Error(historyResult.error || "获取战绩失败");
        }

        setHistory(historyResult.matches || []);
        if (historyResult.matches?.length) {
          loadMatch(historyResult.matches[0].gameId);
        }

        // 设置召唤师资料
        if (overviewResult.success) {
          const profileData = overviewResult.data || {};
          const ranked = profileData.ranked || {};
          const soloQueue =
            ranked.queues?.find((q) => q.queueType === "RANKED_SOLO_5x5") || {};

          setSummonerProfile({
            name: profileData.name || decodedName,
            level: profileData.level || 0,
            profileIconId: profileData.profileIconId || 1,
            tier: soloQueue.tier || "UNRANKED",
            rank: soloQueue.rank || "",
            leaguePoints: soloQueue.leaguePoints || 0,
            wins: soloQueue.wins || 0,
            losses: soloQueue.losses || 0,
          });
        }
      } catch (error) {
        message.error(error.message || "加载数据失败");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [decodedName, navigate]);

  const loadMatch = async (gameId) => {
    setLoading(true);
    try {
      const result = await getMatchDetail(gameId);
      if (!result.success) {
        throw new Error(result.error || "获取对局详情失败");
      }
      setSelectedMatch(result);
    } catch (error) {
      message.error(error.message || "加载对局详情失败");
    } finally {
      setLoading(false);
    }
  };

  const participants = selectedMatch?.participants || [];
  const { blue, red } = groupParticipants(participants);

  return (
    <Layout className="match-layout">
      <Header className="match-header">
        <div className="match-header-inner">
          <Button
            type="primary"
            className="match-back-button"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate("/")}
          >
            返回主页
          </Button>
          <div style={{ flex: 1 }}>
            <Title level={3} style={{ margin: 0, color: "#ffffff" }}>
              {decodedName}
            </Title>
            <Text style={{ color: "rgba(255, 255, 255, 0.85)" }}>
              对局详情与战绩分析
            </Text>
          </div>
        </div>
      </Header>

      <Content className="match-content">
        <div className="match-container">
          {summonerProfile && (
            <Card className="summoner-profile-card" bordered={false}>
              <div className="summoner-profile-content">
                <Avatar
                  size={100}
                  src={`https://ddragon.leagueoflegends.com/cdn/15.1.1/img/profileicon/${summonerProfile.profileIconId}.png`}
                  icon={<UserOutlined />}
                  className="profile-avatar-large"
                />
                <div className="profile-info-section">
                  <div className="profile-name-section">
                    <Title level={2} style={{ margin: 0, color: "#1e293b" }}>
                      {summonerProfile.name}
                    </Title>
                    <Space size="middle" wrap style={{ marginTop: 12 }}>
                      <span className="profile-level-badge">
                        等级 {summonerProfile.level}
                      </span>
                      {summonerProfile.tier !== "UNRANKED" && (
                        <span className="profile-rank-badge">
                          <TrophyOutlined />
                          {summonerProfile.tier} {summonerProfile.rank} -{" "}
                          {summonerProfile.leaguePoints} LP
                        </span>
                      )}
                    </Space>
                  </div>
                  {summonerProfile.tier !== "UNRANKED" && (
                    <div style={{ marginTop: 16 }}>
                      <Space size="large">
                        <Statistic
                          title="胜场"
                          value={summonerProfile.wins}
                          valueStyle={{ color: "#10b981", fontSize: 24 }}
                        />
                        <Statistic
                          title="负场"
                          value={summonerProfile.losses}
                          valueStyle={{ color: "#ef4444", fontSize: 24 }}
                        />
                        <Statistic
                          title="胜率"
                          value={(
                            (summonerProfile.wins /
                              (summonerProfile.wins + summonerProfile.losses)) *
                            100
                          ).toFixed(1)}
                          suffix="%"
                          valueStyle={{ color: "#667eea", fontSize: 24 }}
                        />
                      </Space>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          )}

          <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
            <Col xs={24} lg={8}>
              <Card title="最近战绩" className="match-card" bordered={false}>
                <Spin spinning={loading && !history.length}>
                  <List
                    dataSource={history}
                    renderItem={(item) => (
                      <List.Item
                        actions={[
                          <Button
                            type="link"
                            onClick={() => loadMatch(item.gameId)}
                          >
                            查看详情
                          </Button>,
                        ]}
                      >
                        <List.Item.Meta
                          title={
                            <Space size="small">
                              <Tag
                                color={
                                  item.win || item.result === "Win"
                                    ? "green"
                                    : "red"
                                }
                              >
                                {item.win || item.result === "Win"
                                  ? "胜利"
                                  : "失败"}
                              </Tag>
                              <Text strong>
                                {item.championName || item.championId}
                              </Text>
                            </Space>
                          }
                          description={`模式：${
                            item.gameMode || item.queue
                          } | KDA：${item.kills}/${item.deaths}/${
                            item.assists
                          }`}
                        />
                      </List.Item>
                    )}
                  />
                </Spin>
              </Card>
            </Col>

            <Col xs={24} lg={16}>
              <Spin spinning={loading && !selectedMatch}>
                {selectedMatch ? (
                  <Space
                    direction="vertical"
                    size="large"
                    style={{ width: "100%" }}
                  >
                    <Card className="match-card" bordered={false}>
                      <Row gutter={[16, 16]}>
                        <Col xs={24} md={6}>
                          <Statistic
                            title="胜利方"
                            value={blue[0]?.win ? "蓝色方" : "红色方"}
                            prefix={
                              <TrophyOutlined style={{ color: "#facc15" }} />
                            }
                          />
                        </Col>
                        <Col xs={24} md={6}>
                          <Statistic
                            title="游戏时长"
                            value={selectedMatch.gameInfo?.duration || 0}
                            suffix="分钟"
                            prefix={<ClockCircleOutlined />}
                          />
                        </Col>
                        <Col xs={24} md={6}>
                          <Statistic
                            title="游戏模式"
                            value={selectedMatch.gameInfo?.gameMode || "未知"}
                          />
                        </Col>
                        <Col xs={24} md={6}>
                          <Statistic
                            title="总击杀"
                            value={participants.reduce(
                              (sum, player) => sum + (player.kills || 0),
                              0
                            )}
                            prefix={
                              <FireOutlined style={{ color: "#f87171" }} />
                            }
                          />
                        </Col>
                      </Row>
                    </Card>

                    <Card
                      title="蓝色方"
                      className="match-card"
                      bordered={false}
                    >
                      <Table
                        dataSource={blue}
                        columns={columns}
                        pagination={false}
                        rowKey={(row) => `${row.teamId}-${row.summonerName}`}
                        size="small"
                      />
                    </Card>

                    <Card
                      title="红色方"
                      className="match-card"
                      bordered={false}
                    >
                      <Table
                        dataSource={red}
                        columns={columns}
                        pagination={false}
                        rowKey={(row) => `${row.teamId}-${row.summonerName}`}
                        size="small"
                      />
                    </Card>
                  </Space>
                ) : (
                  <Card className="match-card" bordered={false}>
                    <Text type="secondary">请选择一场对局查看详情。</Text>
                  </Card>
                )}
              </Spin>
            </Col>
          </Row>
        </div>
      </Content>
    </Layout>
  );
}

export default MatchDetailPage;
