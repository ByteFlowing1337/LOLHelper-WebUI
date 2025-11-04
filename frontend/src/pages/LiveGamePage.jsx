import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Layout,
  Button,
  Typography,
  Card,
  Spin,
  Space,
  Tag,
  List,
  message,
} from "antd";
import { ArrowLeftOutlined, ReloadOutlined } from "@ant-design/icons";
import { getLiveGame } from "@/services/api";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

function LiveGamePage() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [liveData, setLiveData] = useState(null);

  const fetchLiveGame = async () => {
    setLoading(true);
    try {
      const result = await getLiveGame();
      if (!result.success) {
        throw new Error(result.error || "获取实时数据失败");
      }
      setLiveData(result.data);
    } catch (error) {
      message.error(error.message || "获取实时数据失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLiveGame();
  }, []);

  const participants = liveData?.players || [];

  return (
    <Layout
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
      }}
    >
      <Header
        style={{ background: "rgba(255,255,255,0.9)", padding: "16px 0" }}
      >
        <div
          style={{
            maxWidth: 1200,
            margin: "0 auto",
            padding: "0 24px",
            display: "flex",
            alignItems: "center",
            gap: 16,
          }}
        >
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate("/")}
          >
            返回
          </Button>
          <div>
            <Title level={3} style={{ margin: 0 }}>
              实时游戏
            </Title>
            <Text type="secondary">实时监控当前对局数据</Text>
          </div>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            onClick={fetchLiveGame}
            style={{ marginLeft: "auto" }}
          >
            刷新数据
          </Button>
        </div>
      </Header>

      <Content style={{ padding: "32px 24px 56px" }}>
        <div style={{ maxWidth: 1200, margin: "0 auto" }}>
          <Card
            style={{
              borderRadius: 14,
              boxShadow: "0 18px 45px rgba(78,101,168,0.2)",
            }}
          >
            <Spin spinning={loading}>
              {liveData ? (
                <Space
                  direction="vertical"
                  size="large"
                  style={{ width: "100%" }}
                >
                  <Space size="large">
                    <Tag color="blue">模式：{liveData.gameMode || "未知"}</Tag>
                    <Tag color="purple">
                      时长：{Math.floor((liveData.gameTime || 0) / 60)} 分钟
                    </Tag>
                  </Space>
                  <List
                    header={<Text strong>参赛选手</Text>}
                    dataSource={participants}
                    renderItem={(item) => (
                      <List.Item>
                        <Space size="large">
                          <Tag color={item.teamId === 100 ? "blue" : "red"}>
                            {item.teamId === 100 ? "蓝色方" : "红色方"}
                          </Tag>
                          <Text strong>{item.summonerName}</Text>
                          <Text type="secondary">
                            英雄：{item.championName}
                          </Text>
                          <Text type="secondary">
                            等级：{item.championLevel}
                          </Text>
                        </Space>
                      </List.Item>
                    )}
                  />
                </Space>
              ) : (
                <Text type="secondary">
                  当前没有正在进行的游戏或数据无法获取。
                </Text>
              )}
            </Spin>
          </Card>
        </div>
      </Content>
    </Layout>
  );
}

export default LiveGamePage;
