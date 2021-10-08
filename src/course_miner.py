import requests  # simplifies getting the HTML pages from Concordia's website
from bs4 import BeautifulSoup  # for parsing course content from HTML pages
import urllib.parse  # for URL encoding course descriptions
import csv  # for storing topics and DBpedia URIs obtained from DBpedia Spotlight
from os import path  # for checking if the topics data file already exists
import io

courses = dict()  # stores all the courses found
topics_filename = 'topics.csv'  # file that stores the course topics obtained from DBpedia Spotlight
students_filename = 'students.csv'  # file that contains the list of (fictional) students
grades_filename = 'grades.csv'  # file that contains the list of grades obtained by the students
turtle_filename = 'knowlegraph.ttl'  # Turtle file containing the RDF triples

# stores course information
class Course:
    def __init__(self):
        self.subject = ''  # course subject (e.g. COMP, SOEN)
        self.num = ''  # course number (e.g. 474)
        self.name = ''  # course name (e.g. Intelligent Systems)
        self.desc = ''  # course description
        self.link = ''  # link to course web page
        self.topics = dict()  # DBpedia links to topics identified in the description by DBpedia Spotlight (topic:URL)


# get the web page containing the course information
resp = requests.get('https://www.concordia.ca/academics/graduate/calendar/current/encs/computer-science-courses.html')

# parse the course information from the web page and store it in Course objects
print('Parsing course information...')
soup = BeautifulSoup(resp.text, 'html.parser')
span_tags = soup.find_all('span', class_='large-text')
for span_tag in span_tags:
    if 1 < len(span_tag.contents) < 13 and 'credit' in str(span_tag.contents[1]) and 'Note:' not in span_tag.b:
        course = Course()
        course_subj_num_name = span_tag.contents[0].string.replace(u'\xa0', ' ')  # removes <b> tags and non-breaking spaces
        course_subj_num_name = course_subj_num_name.split(' ', 1)  # splits on first space to parse course subject
        course.subject = course_subj_num_name[0]
        course_num_name = course_subj_num_name[1].split(" ", 1)  # splits on first space to parse course num
        course.num = course_num_name[0]
        course.name = course_num_name[1]  # the remainder is the course name
        if len(span_tag.contents) > 3:  # check the len of contents because some courses don't have descriptions
            if len(span_tag.contents) > 4 and 'Prerequisite' in str(span_tag.contents[4]):
                course.desc = span_tag.contents[7].strip('\n').strip(' ')
            else:  # the index of the desc for courses with no prerequisites is different
                course.desc = span_tag.contents[3].strip('\n').strip(' ')
        course_id = course.subject + ' ' + course.num + ' ' + course.name  # key for the course dict
        courses[course_id] = course
print('Found ' + str(len(courses)) + ' courses')

# if the topics were already obtained from DBpedia Spotlight, parse them from the CSV file and add them to the Courses
if path.exists(topics_filename):
    print('Parsing course topics from CSV file...')
    topics_file = open(topics_filename, mode='r')
    csv_reader = csv.DictReader(topics_file)
    for row in csv_reader:
        courses[row['course_id']].topics[row['topic']] = row['uri']
else:  # otherwise, send course descriptions to DBpedia Spotlight to get their topics and DBpedia links
    topics_file = open(topics_filename, mode='w', newline='')
    topic_writer = csv.writer(topics_file, delimiter=',')
    topic_writer.writerow(['course_id', 'topic', 'uri'])  # CSV file headers
    print('Retrieving topics from DBpedia Spotlight...')
    requests_sent = 0  # to keep track of how many courses didn't have a description
    for course_id in courses:
        if len(courses[course_id].desc) > 0:
            url_encoded_desc = urllib.parse.quote(courses[course_id].desc)  # description must be url encoded
            resp_format = {'accept': 'application/json'}
            resp = requests.get('https://api.dbpedia-spotlight.org/en/annotate?text=' + url_encoded_desc, headers=resp_format)
            requests_sent += 1
            try:
                resp_content = resp.json()
            except ValueError:  # catches JSONDecodeErrors that seem to randomly occur due to 403 Forbidden responses
                print('(!) Invalid response for ' + course_id + ' | HTTP ' + str(resp.status_code))
            else:  # response is a dict; the URIs are in a list with the key 'Resources'
                if 'Resources' in resp_content:  # for some courses, DBpedia Spotlight doesn't find any links
                    dbpedia_links = resp_content['Resources']
                    for link in dbpedia_links:
                        topic = link['@surfaceForm'].lower()
                        uri = link['@URI']
                        courses[course_id].topics[topic] = uri
                        topic_writer.writerow([course_id, topic, uri])
    print('Topic and URI requests sent for ' + str(requests_sent) + ' courses')
print('Course topics and URIs added to courses')

# output course data to a Turtle file
print('Writing course data to a Turtle file...')
turtle_file = io.open(turtle_filename, mode='w', encoding='utf8')
# add the headers
turtle_file.write('@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .\n' +
                  '@prefix rdfs:   <http://www.w3.org/2000/01/rdf-schema#> .\n' +
                  '@prefix dbr:    <http://dbpedia.org/resource/> .\n' +
                  '@prefix dbo:    <http://dbpedia.org/ontology/> .\n' +
                  '@prefix foaf:   <http://xmlns.com/foaf/spec/> .\n' +
                  '@prefix uni:    <http://localhost:3030/assignment1/> .\n')  # custom ontology for describing university courses
turtle_file.write('\n')
# add the Course class and course properties definitions
turtle_file.write('uni:Course a rdfs:Class ;\n' +
                  '  rdfs:label    "Course"@en ;\n' +
                  '  rdfs:comment  "A course at a university." .\n\n')
turtle_file.write('uni:subject a rdf:Property ;\n' +
                  '  rdfs:label    "Subject"@en ;\n' +
                  '  rdfs:comment  "The course subject (e.g. COMP for Computer Science)." ;\n' +
                  '  rdfs:domain   uni:Course .\n\n')
turtle_file.write('uni:number a rdf:Property ;\n' +
                  '  rdfs:label    "Number"@en ;\n' +
                  '  rdfs:comment  "The course number, usually composed of 3 or 4 digits." ;\n' +
                  '  rdfs:domain   uni:Course .\n\n')
turtle_file.write('uni:name a rdf:Property ;\n' +
                  '  rdfs:label    "Name"@en ;\n' +
                  '  rdfs:comment  "The course name (e.g. Intelligent Systems)." ;\n' +
                  '  rdfs:domain   uni:Course .\n\n')
turtle_file.write('uni:description a rdf:Property ;\n' +
                  '  rdfs:label    "Description"@en ;\n' +
                  '  rdfs:comment  "The course description" ;\n' +
                  '  rdfs:domain   uni:Course .\n\n')
turtle_file.write('uni:taught_at a rdf:Property ;\n' +
                  '  rdfs:label    "Taught at"@en ;\n' +
                  '  rdfs:comment  "The academic institution at which the course is taught." ;\n' +
                  '  rdfs:domain   uni:Course ;\n' +
                  '  rdfs:range    dbo:University .\n\n')
turtle_file.write('uni:topic a rdfs:Class ;\n' +
                  '  rdfs:label    "has topic"@en ;\n'
                  '  rdfs:comment  "Topic " .\n\n')
turtle_file.write('uni:hasTopic a rdf:Property ;\n' +
                  '  rdfs:label    "has the topic"@en ;\n'
                  '  rdfs:comment  "predicate that denotes a course having a topic " .\n\n')
turtle_file.write('uni:label a rdf:Property ;\n' +
                  '  rdfs:label    "Topic"@en ;\n'
                  '  rdfs:comment  "predicate that denotes that a course has a specific topic " .\n\n')
turtle_file.write('uni:link a rdf:Property ;\n' +
                  '  rdfs:label    "URI is"@en ;\n'
                  '  rdfs:comment  "predicate that denotes a link to URI " .\n\n')


#appends additional predicates for Student from another turtle file
with open("students.ttl") as fp:
    student_file = fp.read()

turtle_file.write(student_file)

# add the course information
first_course = True  # flag to avoid adding a . at the start of the first Course
for course_id in courses:
    if not first_course:
        turtle_file.write(' .\n\n')  # adds . at the end of previous Course for proper Turtle syntax
    turtle_file.write('uni:' + courses[course_id].subject + courses[course_id].num + ' a uni:Course ;\n' +
                      '  uni:taught_at    dbr:Concordia_University ;\n'
                      '  uni:subject      "' + courses[course_id].subject + '" ;\n'
                      '  uni:number       "' + courses[course_id].num + '" ;\n'
                      '  uni:name         "' + courses[course_id].name + '"')
    if len(courses[course_id].desc) > 0:
        turtle_file.write(' ;\n')  # adds ; at the end of name line
        turtle_file.write('  uni:description  "' + courses[course_id].desc + '" ')
        if len(courses[course_id].topics) > 0:
            for topic in courses[course_id].topics:
                turtle_file.write(' ;\n')  # adds ; at the end of description line or previous topics
                w = courses[course_id].topics[topic]
                x = w.replace("–", "_")
                x = x.replace("(", "")
                x = x.replace(")", "")
                y = x[28:]
                turtle_file.write('  uni:hasTopic        uni:' + y + ' ')
    first_course = False
turtle_file.write(' .\n\n')  # adds . at the end of the last Course


#adds label and URI link to each Topic object
for course_id in courses:
        if len(courses[course_id].topics) > 0:
            for topic in courses[course_id].topics:
                w = courses[course_id].topics[topic]
                x = w.replace("–", "_")
                x = x.replace("(", "")
                x = x.replace(")", "")
                y = x[28:]
                turtle_file.write('uni:'+y + ' a uni:topic .\n')
                turtle_file.write('uni:'+y + ' rdfs:label "' + y + '" . \n')
                turtle_file.write('uni:'+y + ' uni:link <' + x + '> . \n') # adds ; at the end of description line or previous topics

# import student list from CSV file and add them to the Turtle file
students_file = open(students_filename, mode='r')
csv_reader = csv.DictReader(students_file)
for row in csv_reader:
    turtle_file.write('uni:' + row['first'] + ' a uni:Student ;\n' +
                      '  foaf:givenName   "' + row['first'] + '" ;\n' +
                      '  foaf:familyName    "' + row['last'] + '" ;\n' +
                      '  uni:enrolled_at  dbr:Concordia_University ;\n' +
                      '  foaf:mbox    "' + row['mbox'] + '" ;\n' +
                      '  uni:hasStudentID           "' + row['id'] + '" .\n\n')

# import grades from CSV file and add them to the Turtle
grade_id = 1  # to generate ID numbers for the grade records
grades_file = open(grades_filename, mode='r')
csv_reader = csv.DictReader(grades_file)
for row in csv_reader:
    turtle_file.write('uni:' + row['student'] + " ")
    if row['grade'] == 'A':
        turtle_file.write("uni:gotAin ")
    if row['grade'] == 'B':
        turtle_file.write("uni:gotBin ")
    if row['grade'] == 'C':
        turtle_file.write("uni:gotCin ")
    if row['grade'] == 'D':
        turtle_file.write("uni:gotDin ")
    if row['grade'] == 'F':
        turtle_file.write("uni:gotFin ")
    turtle_file.write('uni:' + row['course'] + " .\n")


# for testing
print()
print('COURSE LIST:')
print()
for course_id in courses:
    print(courses[course_id].subject + ' ' + courses[course_id].num + ': ' + courses[course_id].name + ' - ' + courses[course_id].desc)
    print(courses[course_id].topics)