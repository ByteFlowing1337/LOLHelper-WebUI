import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Layout,
  Button,
  Typography,
  Card,
  Table,
  Tag,
  message,
  Spin,
} from "antd";
import { ArrowLeftOutlined } from "@ant-design/icons";
import { getTftHistory } from "@/services/api";

const { Header, Content } = Layout;
const { Title, Text } = Typography;

const columns = [
  {
    title: "排名",
    dataIndex: "placement",
    key: "placement",
    render: (value) => {
      let color = "default";
      if (value === 1) color = "gold";
      else if (value <= 4) color = "green";
      return <Tag color={color}>#{value}</Tag>;
    },
  },
  {
    title: "等级",
    dataIndex: "level",
    key: "level",
  },
  {
    title: "时长",
    dataIndex: "gameDuration",
    key: "gameDuration",
    render: (value) => `${Math.floor((value || 0) / 60)} 分钟`,
  },
  {
    title: "特质",
    dataIndex: "traits",
    key: "traits",
    render: (traits) =>
      traits ? traits.map((trait) => trait.name).join(" / ") : "未知",
  },
];

function TFTSummonerPage() {
  const { summonerName } = useParams();
  const navigate = useNavigate();
  const decodedName = decodeURIComponent(summonerName || "");
  const [loading, setLoading] = useState(false);
  const [matches, setMatches] = useState([]);

  useEffect(() => {
    if (!decodedName) {
      navigate("/tft");
      return;
    }

    const fetchTftHistory = async () => {
      setLoading(true);
      try {
        const result = await getTftHistory(decodedName);
        if (!result.success) {
          throw new Error(result.error || "获取 TFT 战绩失败");
        }
        setMatches(result.matches || []);
      } catch (error) {
        message.error(error.message || "获取 TFT 战绩失败");
      } finally {
        setLoading(false);
      }
    };

    fetchTftHistory();
  }, [decodedName, navigate]);

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
              TFT 战绩
            </Title>
            <Text type="secondary">召唤师：{decodedName}</Text>
          </div>
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
              <Table
                rowKey={(row) => row.gameId}
                dataSource={matches}
                columns={columns}
                pagination={{ pageSize: 10 }}
              />
            </Spin>
          </Card>
        </div>
      </Content>
    </Layout>
  );
}

export default TFTSummonerPage;
