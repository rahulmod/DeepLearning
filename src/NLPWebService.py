#You can expose Stanford NLP as a web service and call it as a service
from stanfordcorenlp import StanfordCoreNLP

# nlp = StanfordCoreNLP('http://127.0.0.1:9000')
# sentence = 'Guangdong University of Foreign Studies is located in Guangzhou.'
# output = nlp.annotate(sentence, properties={
#     "annotators": "tokenize,ssplit,parse,sentiment",
#     "outputFormat": "json",
#     # Only split the sentence at End Of Line. We assume that this method only takes in one single sentence.
#         "ssplit.eolonly": "true",
# # Setting enforceRequirements to skip some annotators and make the process faster
# "enforceRequirements": "false"
# })
# nlp.close()
# print output

# Simple usage

nlp = StanfordCoreNLP(r'G:\JavaLibraries\stanford-corenlp-full-2018-02-27')

sentence = 'Guangdong University of Foreign Studies is located in Guangzhou.'
print 'Tokenize:', nlp.word_tokenize(sentence)
print 'Part of Speech:', nlp.pos_tag(sentence)
print 'Named Entities:', nlp.ner(sentence)
print 'Constituency Parsing:', nlp.parse(sentence)
print 'Dependency Parsing:', nlp.dependency_parse(sentence)

nlp.close() # Do not forget to close! The backend server will consume a lot memery.