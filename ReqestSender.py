import requests
from settings import settings
import Commands
import io

config = settings()
# styles = [32500,
# 32501,
# 23508,
# 23509,
# 23515,
# 20226,
# 20229,
# 20753,
# 20230,
# 20255,
# 31723,
# 21954,
# 20259,
# 20256,
# 23556,
# 32492,
# 32491,
# 32487,
# 32486,
# 32493,
# 23481,
# 20225,
# 32494,
# 31670,
# 32489,
# 32488,
# 32490,
# 12782,
# 23561,
# 25544,
# 23471,
# 20968,
# 22464,
# 32454,
# 22453,
# 32430,
# 23472,
# 20993,
# 25126,
# 25739,
# 25543,
# 25201,
# 25203,
# 24794,
# 25357,
# 26255,
# 21159,
# 22575,
# 25938,
# ]
# for style in styles:
#     params = {'values': str(style), 'size': 1}
#     #params = {'lyrics': 'black', 'size': 1}
#     r = requests.post("http://muzis.ru/api/stream_from_values.api", data=params)
#     fid = open("D:/ChatBot/WaveRiderChatbot/test_lyrics/" + str(style) + '.txt', 'w')
#     parsed_string = r.json()
#     a = parsed_string['songs'][0]['lyrics']
#     b = a.encode('cp1251')
#     fid.write(b)
#     fid.close()

class RequestSender:

     def __init__(self):
         self.logger = Commands.workWithLog(config.log)
         self.matching = dict()
         self.CNNstyles = [];
         self.loadMatching()

     def loadMatching(self):
         with io.open(config.database_name) as file:
             for idx, line in enumerate(file):
                 lineSplit = line.strip('\n').split(' ')
                 self.CNNstyles.append(str(lineSplit[0]))
                 self.matching[str(lineSplit[0])] = lineSplit[1:len(lineSplit)]
         return

     def parseVector(self, vector):
         #parsing
         targetStyle = None
         for idx, value in enumerate(vector):
             elem = self.matching[self.CNNstyles[idx]]
             minValue = 0.0#elem[0]
             maxValue = 1.0#elem[1]
             if (value > minValue) & (value < maxValue):
                 targetStyle = elem[2]
                 break
         return targetStyle

     def sendRequest(self, style):
         params = {'values': str(style), 'size': 100}
         try:
            r = requests.post("http://muzis.ru/api/stream_from_values.api", data=params)
            parsed_string = r.json()

            song = parsed_string['songs'][0]['lyrics']
            lyrics = song.encode('utf-8')
         except:
             self.logger.siteWarning()
         return

RS = RequestSender()
targetStyle = RS.parseVector([0.02495627,  0.01625971, 0.05735248,  0.03012436, 0.01382483,  0.01830654,
  0.02935727,  0.02657287,  0.02752874,  0.00897765,  0.01500904,  0.01215811,
  0.02771803,  0.23560295,  0.01554973,  0.01857543, 0.03318637,  0.17324899,
  0.18867876,  0.02701183])
RS.sendRequest(targetStyle)


