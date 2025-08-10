from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "Apple123"))

def get_keyword_faculty_network(selected_keyword):
    selected_keyword = selected_keyword.lower() 
    query = """
    MATCH (k:KEYWORD)
    WHERE toLower(k.name) = toLower($kw)
    WITH k
    MATCH (k)<-[:INTERESTED_IN]-(f:FACULTY)-[:INTERESTED_IN]->(other:KEYWORD)
    RETURN f.name AS faculty, k.name AS keyword, collect(DISTINCT other.name) AS co_keywords
    LIMIT 20
    """
    with driver.session(database="academicworld") as session:
        result = session.run(query, kw=selected_keyword)
        data = []
        for row in result:
            data.append({
                "faculty": row["faculty"],
                "keyword": row["keyword"],
                "co_keywords": row["co_keywords"]
            })
        return data
    

driver = GraphDatabase.driver(
    "bolt://localhost:7687", 
    auth=("neo4j", "Apple123"), 
    encrypted=False
)

def get_all_neo4j_keywords():
    query = """
    MATCH (f:FACULTY)-[:INTERESTED_IN]->(k:KEYWORD)
    RETURN DISTINCT k.name AS keyword
    ORDER BY keyword
    """
    with driver.session(database="academicworld") as session:
        result = session.run(query)
        return [row["keyword"] for row in result]







