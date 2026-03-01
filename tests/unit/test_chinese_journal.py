"""Unit tests for Chinese journal template."""

from __future__ import annotations

from md2pdf_pro.templates import get_chinese_journal_params


class TestChineseJournalParams:
    """Tests for get_chinese_journal_params function."""

    def test_empty_params(self):
        """Test with no parameters."""
        params = get_chinese_journal_params()
        assert params == {}

    def test_journal_info(self):
        """Test journal information parameters."""
        params = get_chinese_journal_params(
            journal_title="计算机学报",
            journal_vol="45",
            journal_issue="3",
            journal_year="2024",
        )
        assert params["journal-title"] == "计算机学报"
        assert params["journal-vol"] == "45"
        assert params["journal-issue"] == "3"
        assert params["journal-year"] == "2024"

    def test_article_info(self):
        """Test article information parameters."""
        params = get_chinese_journal_params(
            article_title="深度学习在计算机视觉中的应用",
            doi="10.12345/jos.2024.001",
            article_id="1001-0505(2024)03-0001-08",
        )
        assert params["title"] == "深度学习在计算机视觉中的应用"
        assert params["doi"] == "10.12345/jos.2024.001"
        assert params["article-id"] == "1001-0505(2024)03-0001-08"

    def test_author_info(self):
        """Test author information parameters."""
        params = get_chinese_journal_params(
            author="张三, 李四",
            affiliation="清华大学计算机科学与技术系",
            email="zhangsan@tsinghua.edu.cn",
        )
        assert params["author"] == "张三, 李四"
        assert params["affiliation"] == "清华大学计算机科学与技术系"
        assert params["email"] == "zhangsan@tsinghua.edu.cn"

    def test_abstract_keywords(self):
        """Test abstract and keywords."""
        params = get_chinese_journal_params(
            abstract="本文研究了...",
            keywords="深度学习, 计算机视觉, 图像识别",
            abstract_en="This paper studies...",
            keywords_en="deep learning, computer vision, image recognition",
        )
        assert params["abstract"] == "本文研究了..."
        assert params["keywords"] == "深度学习, 计算机视觉, 图像识别"
        assert params["abstract-en"] == "This paper studies..."
        assert (
            params["keywords-en"] == "deep learning, computer vision, image recognition"
        )

    def test_full_params(self):
        """Test with all parameters."""
        params = get_chinese_journal_params(
            journal_title="软件学报",
            article_title="面向云原生的微服务架构设计",
            subtitle="基于Kubernetes的研究",
            author="王五, 赵六",
            affiliation="北京大学软件研究所",
            email="wangwu@pku.edu.cn",
            abstract="随着云原生技术的快速发展...",
            keywords="云原生, 微服务, Kubernetes",
            abstract_en="With the rapid development of cloud native technology...",
            keywords_en="cloud native, microservices, Kubernetes",
            doi="10.13345/jss.2024.002",
            article_id="1000-9825(2024)05-0015-10",
            journal_vol="35",
            journal_issue="8",
            journal_year="2024",
            journal_date="2024-05-15",
        )

        assert params["journal-title"] == "软件学报"
        assert params["title"] == "面向云原生的微服务架构设计"
        assert params["subtitle"] == "基于Kubernetes的研究"
        assert params["author"] == "王五, 赵六"
        assert params["affiliation"] == "北京大学软件研究所"
        assert params["email"] == "wangwu@pku.edu.cn"
        assert "云原生" in params["keywords"]
        assert params["doi"] == "10.13345/jss.2024.002"
        assert params["journal-vol"] == "35"
        assert params["journal-issue"] == "8"
