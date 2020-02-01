# -*- coding: utf-8 -*-
"""Copy of Assignment1.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1dZe0nO1Mz7WLXH640WxrfI4FEmsH2k2c
"""



import apache_beam as beam

#import print library
import logging

#import pipeline options.
from apache_beam.options.pipeline_options import  PipelineOptions

#Set log level to info
root = logging.getLogger()
root.setLevel(logging.INFO)



try:
    import urllib.request as urllib2
except ImportError:
    import urllib2
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import io 
from nltk.corpus import stopwords 
import nltk
nltk.download('stopwords')

from tokenizers import SentencePieceBPETokenizer

# Initialize a tokenizer
tokenizer = SentencePieceBPETokenizer()

# Then train it!
tokenizer.train('Trained_words.txt')

# And finally save it somewhere
tokenizer.save("tokenizer", "my-bpe")

# Initialize a tokenizer
vocab = "tokenizer/my-bpe-vocab.json"
merges = "tokenizer/my-bpe-merges.txt"
tokenizer = SentencePieceBPETokenizer(vocab, merges)

#scrape from input to output
def input_to_output():
    inputs_pattern = 'data/export_dataframe.csv'
    df = pd.read_csv(inputs_pattern)
    output_csv = pd.DataFrame(columns=['cik', 'year', 'Filings', 'link'])
    counter=0
    quarter = ['QTR1','QTR2','QTR3','QTR4']
    for i in quarter:
        for index, row in df.iterrows():
        #print(index)
        #print(row['cik'])
        #print(row['year'])
        #print(row['Filings'])
        #####Get the Master Index File for the given Year
            url='https://www.sec.gov/Archives/edgar/full-index/%s/%s/master.idx'%(str(row['year']),i)
            response = urllib2.urlopen(url)
            string_match1 = 'edgar/data/'
            element2 = None
            element3 = None
            element4 = None
            #print(url)
            #print(response)
            ###Go through each line of the master index file and find given CIK #and
                #FILE (10-K) and extract the text file path
            for line in response:
                line=line.decode('utf-8')
                if str(row['cik']) in line and str(row['Filings']) in line:
                    for element in line.split(' '):
                        if string_match1 in element:
                            element2=element.split('|')
                            for element3 in element2:
                                if string_match1 in element3:
                                    element4 = element3
                                    url3 = 'https://www.sec.gov/Archives/'+ element4
                                    response3 = urllib2.urlopen(url3)
                                    #print (url3)
                                    a=row['cik']
                                    b=row['year']
                                    c=row['Filings']
                                    output_csv.loc[counter]=[a,b,c,url3]
                                    counter=counter+1
                                    output_csv.to_csv('outputs/output.csv')
    return output_csv

output_csv = input_to_output()

#scrape text files
def scrape_textfiles():
  inputs_pattern = 'outputs/output.csv'
  df = pd.read_csv(inputs_pattern)
  text_list = []
  for index, row in df.iterrows():
      cik = df['cik'][index]
      year = df['year'][index]
      filing = df['Filings'][index]
      link = df['link'][index]
      url1 = requests.get(link)
      data = url1.text
      #soup = BeautifulSoup(data, 'html.parser')
      #with open("cleanedHtml.txt", "w") as file:
      #print(soup.prettify())
          #file.write(soup.get_text())
      #file.close()
      #print(type(soup.get_text()))
      parsed_html = BeautifulSoup(data, "lxml")
      #with open("parsed_html.txt", "w+", encoding='utf-8') as f:
          #f.write(''.join(parsed_html.html.findAll(text=True)))
          #f.write(parsed_html.get_text())
      text_list.append([link[:-1],parsed_html.get_text(),cik, year, filing])
      #f.close()
  df_text_list = pd.DataFrame(text_list)
  df_text_list.to_csv('outputs/text_list.csv') 
  return text_list

text_list = scrape_textfiles()

def create_text_files():
  for j in range(0,len(text_list)):
      string = text_list[j][1]
      new_str = re.sub('[^a-zA-Z]', ' ', string)
      new_str2 = ' '.join(word for word in new_str.split(' ') if len(word) > 1)
      open('text_files/TextFiles%s.txt'%j, 'w', encoding='utf-8').write(string)

create_text_files()

class stopwords_removal(beam.DoFn):
  def remove_stopwords(self,element):
    # stopwords_list = set(stopwords.words('english')) 
    # print(stopwords_list)
    stop_words = set(stopwords.words('english'))
    #inputs_pattern = 'word_list.csv'
    #df = pd.read_csv(inputs_pattern)
    #text_list = df.values.tolist()
    for k in range(0,len(text_list)):
        file1 = open("text_files/TextFiles%s.txt"%k, encoding='utf-8') 
        line = file1.read()# Use this to read file content as a stream: 
        element = line.split()
        for r in element:
            if not r in stop_words:
                appendFile = open('stopwords/stopWordsRemoved%s.txt'%k,'a', encoding='utf-8')
                appendFile.write(" "+r)  
                appendFile.close()
    return

class Tokenize(beam.DoFn):
  def process(self, element):
    line = element.split()
    encoded = tokenizer.encode_batch(line)
    return

class Word_count(beam.DoFn):
  def process(self,element,):

    negative = open("categories/Negative.txt").read().split()
    positive = open("categories/Positive.txt").read().split()
    uncertainty = open("categories/Uncertainty.txt").read().split()
    litigious = open("categories/Litigious.txt").read().split()
    strongmodal = open("categories/StrongModal.txt").read().split()
    weakmodal = open("categories/WeakModal.txt").read().split()
    constraining = open("categories/Constraining.txt").read().split()



    # Open the file in read mode 
    text1 = element.split()

    count_list = []
    #count_csv = pd.DataFrame(columns=['Word', 'Wordlist', 'Count'])
    for w in set(text1):
        if w in negative:
            count_list.append([w,"negative",text1.count(w)])
        elif w in positive:
            count_list.append([w,"positive",text1.count(w)])
        elif w in uncertainty:
            count_list.append([w,"uncertainty",text1.count(w)])
        elif w in litigious:
            count_list.append([w,"litigious",text1.count(w)])
        elif w in strongmodal:
            count_list.append([w,"strongmodal",text1.count(w)])
        elif w in weakmodal:
            count_list.append([w,"weakmodal",text1.count(w)])
        elif w in constraining:
            count_list.append([w,"constraining",text1.count(w)])
    #count_csv = pd.DataFrame(count_list)
    #count_csv.columns=['Word', 'Wordlist', 'Count']
    #count_csv.to_csv('word_count.csv')
    return count_list

def split_words(text):
  return text.split(' ')

#Create a pipeline
plOps = beam.Pipeline(options=PipelineOptions())

txt_files = (
          plOps | 'Read lines' >> beam.io.ReadFromText('text_files/*.txt')
      )

      clean_regex = (
          txt_files | 'Regex' >> beam.Regex.replace_all(r'[^a-zA-Z]', ' ')
      )

      split_word = (
          clean_regex | 'Flatten Words' >> beam.FlatMap(split_words)
      )

      remove_space = (
          split_word | 'Remove blanks' >> beam.Filter(lambda x: x.strip())
      )
       
      word_counts = (
          remove_space | 'Word count' >> beam.ParDo(Word_count())
                       | 'Write word count' >> beam.io.WriteToText('word_count', file_name_suffix='.txt')
      )

def removestopwords():
   stopwords = set(stopwords.words('english')) 
   return stop_words

def match_stopwords():
    #words = pipeline_demo.split()
    for r in pipeline_demo:
      if r in stopwords_list:
        r = r.replace(word, "")
    return r

def counter_generation(x):
  return (counter+1 , x)

def stopwords_list():
    inputs_pattern = 'stopwords_list.csv'
    df = pd.read_csv(inputs_pattern)
    return df

# Run the pipeline
result = plOps.run()
#  wait until pipeline processing is complete
result.wait_until_finish()