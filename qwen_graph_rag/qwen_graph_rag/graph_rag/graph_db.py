from neo4j import GraphDatabase


class KnowledgeGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def create_schema(self):
        """创建知识图谱schema"""
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT FOR (e:Entity) REQUIRE e.id IS UNIQUE")
            session.run("CREATE CONSTRAINT FOR (c:Concept) REQUIRE c.name IS UNIQUE")
            session.run("CREATE INDEX FOR (e:Entity) ON (e.type)")
            session.run("CREATE INDEX FOR (c:Concept) ON (c.category)")

    def add_entity(self, entity_id, entity_type, properties):
        """添加实体节点"""
        with self.driver.session() as session:
            session.run("""
                MERGE (e:Entity {id: $entity_id})
                SET e.type = $entity_type, e += $properties
            """, entity_id=entity_id, entity_type=entity_type, properties=properties)

    def add_relationship(self, from_id, to_id, rel_type, properties=None):
        """添加关系边"""
        with self.driver.session() as session:
            session.run("""
                MATCH (a:Entity {id: $from_id})
                MATCH (b:Entity {id: $to_id})
                MERGE (a)-[r:$rel_type]->(b)
                SET r += $properties
            """, from_id=from_id, to_id=to_id, rel_type=rel_type, properties=properties or {})

    def query_entities(self, entity_type=None, limit=100):
        """查询实体节点"""
        with self.driver.session() as session:
            if entity_type:
                result = session.run("""
                    MATCH (e:Entity {type: $entity_type})
                    RETURN e
                    LIMIT $limit
                """, entity_type=entity_type, limit=limit)
            else:
                result = session.run("""
                    MATCH (e:Entity)
                    RETURN e
                    LIMIT $limit
                """, limit=limit)
            return [record["e"] for record in result]

    def close(self):
        """关闭连接"""
        self.driver.close()
