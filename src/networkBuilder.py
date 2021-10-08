import rdflib

graph = rdflib.Graph()
graph.parse("knowlegraph.ttl", format='turtle')

# for s, p, o in graph:
#     print(s, p, o)

query1 = graph.query(
    """SELECT DISTINCT ?s ?p ?o
    WHERE {
        ?s ?p ?o} """)
print("Query 1: \nTotal number of triples in the KB.\n")
print("Number of triples in KB: " + str(len(query1)))

query2a = graph.query(
    """SELECT DISTINCT ?s
    WHERE {
        ?s a uni:Student } """)
print("\nQuery 2: \nTotal number of students, courses, and topics.\n")
print("Number of students: " + str(len(query2a)))
query2b = graph.query(
    """SELECT DISTINCT ?s
    WHERE { 
        ?s a uni:Course } """)
print("Number of courses: " + str(len(query2b)))

query2c = graph.query(
    """SELECT DISTINCT  ?o
    WHERE {
        ?o a uni:topic} """)
print("Number of topics: " + str(len(query2c)))

query3 = graph.query(
    """SELECT ?label ?uri
    WHERE {
        uni:COMP6281 uni:hasTopic ?x .
        ?x rdfs:label ?label .
        ?x uni:link ?uri .
        } """)

print("\nQuery 3: \nFor a course (COMP6281), list all covered topics.\n")
for row in query3:
    print("%s %s" % row)


query4 = graph.query(
    """SELECT DISTINCT  ?name ?grade ?class
    WHERE {
        ?x a uni:Student .
        ?x foaf:givenName "Agnes" .
        ?x foaf:givenName ?name .
        ?z a uni:Course .
        ?x ?y ?z .
        ?z uni:name ?class .
        ?y rdfs:label ?grade .
        {?x uni:gotAin ?z .}
        UNION
        {?x uni:gotBin ?z .}
        UNION
        {?x uni:gotCin ?z .}
        UNION
        {?x uni:gotDin ?z .}
    }""")

print("\nQuery 4: \nFor a given student, list all courses this student completed.\n")
for row in query4:
    print("%s %s %s" % row)

query5 = graph.query(
    """SELECT ?student
    WHERE {
        ?c uni:hasTopic uni:Scalability .
        {?s uni:gotAin ?c .}
        UNION
        {?s uni:gotBin ?c .}
        UNION
        {?s uni:gotCin ?c .}
        UNION
        {?s uni:gotDin ?c .}
        ?s foaf:givenName ?student .
    } """)

print("\nQuery 5: \nFor a given topic (Scalability), list all students that are familiar with the topic.\n")
print("All 10 students took COMP6231 but Janet & Ingrid failed:")
for row in query5:
    print("%s" % row)


query6 = graph.query(
    """SELECT DISTINCT ?topic
    WHERE {
        ?s a uni:Student .
        ?s uni:hasStudentID "C2C2C2C2" .
        {?s uni:gotAin ?c .}
        UNION
        {?s uni:gotBin ?c .}
        UNION
        {?s uni:gotCin ?c .}
        UNION
        {?s uni:gotDin ?c .}
        ?c uni:hasTopic ?t .
        ?t rdfs:label ?topic .
        } """)

print("\nQuery 6: \nFor a student (Cindy), list all topics they know.\n")
for row in query6:
    print("%s" % row)


