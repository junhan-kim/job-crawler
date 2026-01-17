"""에이전트 노드 단위 테스트."""


from agent.models import ParsedQuery
from agent.nodes.plan import _build_keywords, _create_search_plan
from agent.nodes.synthesize import _apply_filters, _generate_response


class TestPlanNode:
    """plan 노드 테스트."""

    def test_build_keywords_with_role_and_skills(self):
        """역할과 스킬이 있으면 키워드 목록 생성."""
        conditions = ParsedQuery(role="백엔드", skills=["Python", "Django"])
        keywords = _build_keywords(conditions)

        assert "백엔드" in keywords
        assert "Python" in keywords
        assert "Django" in keywords

    def test_build_keywords_empty(self):
        """조건이 없으면 빈 키워드."""
        conditions = ParsedQuery()
        keywords = _build_keywords(conditions)

        assert keywords == []

    def test_create_search_plan(self):
        """검색 계획 생성."""
        keywords = ["백엔드", "Python"]
        conditions = ParsedQuery(experience=3, location="서울")

        plan = _create_search_plan(keywords, conditions)

        assert plan.keywords == keywords
        assert plan.search_keyword == "백엔드 Python"
        assert plan.filters.experience == 3
        assert plan.filters.location == "서울"


class TestSynthesizeNode:
    """synthesize 노드 테스트."""

    def test_apply_filters_by_location(self, sample_job_posting):
        """지역 필터링."""
        results = [sample_job_posting]
        conditions = ParsedQuery(location="서울")

        filtered = _apply_filters(results, conditions)

        assert len(filtered) == 1

    def test_apply_filters_no_match(self, sample_job_posting):
        """매칭 안되면 필터링."""
        results = [sample_job_posting]
        conditions = ParsedQuery(location="부산")

        filtered = _apply_filters(results, conditions)

        assert len(filtered) == 0

    def test_generate_response_with_results(self):
        """결과 있을 때 응답 생성."""
        conditions = ParsedQuery(role="백엔드", skills=["Python"])
        results = [{"title": "test"}]

        response = _generate_response(conditions, results)

        assert "백엔드" in response
        assert "Python" in response
        assert "1개" in response

    def test_generate_response_empty_conditions(self):
        """조건 없을 때 응답 생성."""
        conditions = ParsedQuery()
        results = [{"title": "test"}]

        response = _generate_response(conditions, results)

        assert "전체" in response
