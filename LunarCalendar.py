import csv
import datetime
import os


class LunarCalendar:
    """
    LunarCalendar by Adrian I. Lam (2019),
    a Python 3 port of the JavaScript LunarCalendar by zzyss86,
    available at <https://github.com/zzyss86/LunarCalendar>.

    This is only a partial port. I have ported
    LunarCalendar.solarToLunar(year, month, day) and
    LunarCalendar.lunarToSolar(year, month, day) only,
    and have ignored everything related to holidays.

    Since the original author did not specify any license, I will
    also not license this script. This script comes with no warranties,
    expressed or implied. In particular, the warranties of merchantability,
    fitness for a particular purpose and noninfringement are disclaimed.
    """

    def __formatDayD4(self, month, day):
        month = month + 1
        month = '0' + str(month) if month < 10 else str(month)
        day = '0' + str(day) if day < 10 else str(day)
        return 'd' + month + day

    __minYear = 1890
    __maxYear = 2100

    __heavenlyStems = ['甲', '乙', '丙', '丁', '戊',
                       '己', '庚', '辛', '壬', '癸']  # 天干
    __earthlyBranches = ['子', '丑', '寅', '卯', '辰', '巳',
                         '午', '未', '申', '酉', '戌', '亥']  # 地支
    __zodiac = ['鼠', '牛', '虎', '兔', '龍', '蛇',
                '馬', '羊', '猴', '雞', '狗', '豬']  # 對應地支十二生肖
    __solarTerm = ['小寒', '大寒', '立春', '雨水', '驚蟄', '春分',
                   '清明', '穀雨', '立夏', '小滿', '芒種', '夏至',
                   '小暑', '大暑', '立秋', '處暑', '白露', '秋分',
                   '寒露', '霜降', '立冬', '小雪', '大雪', '冬至']  # 二十四節氣
    __monthCn = ['正', '二', '三', '四', '五', '六',
                 '七', '八', '九', '十', '十一', '十二']
    __dateCn = ['初一', '初二', '初三', '初四', '初五', '初六',
                '初七', '初八', '初九', '初十', '十一', '十二',
                '十三', '十四', '十五', '十六', '十七', '十八',
                '十九', '二十', '廿一', '廿二', '廿三', '廿四',
                '廿五', '廿六', '廿七', '廿八', '廿九', '三十', '卅一']

    # 1890 - 2100 年的農曆數據
    # 數據格式：[0,2,9,21936]
    # [閏月所在月，0為沒有閏月;
    #  *正月初一對應公曆月;
    #  *正月初一對應公曆日;
    #  *農曆每月的天數的數組（需轉換為二進制,得到每月大小，
    #                        0=小月(29日),1=大月(30日)）;]
    __lunarInfo = []
    __dir = os.path.dirname(os.path.realpath(__file__))
    with open(os.path.join(__dir, 'lunarInfo.csv')) as __lunarInfoCSV:
        for __row in csv.reader(__lunarInfoCSV):
            __lunarInfo.append([int(x) for x in __row])

    # 二十四節氣數據，節氣點時間（單位是分鐘）
    # 從0小寒起算
    __termInfo = [0, 21208, 42467, 63836, 85337, 107014, 128867, 150921,
                  173149, 195551, 218072, 240693, 263343, 285989, 308563,
                  331033, 353350, 375494, 397447, 419210, 440795, 462224,
                  483532, 504758]

    def __init__(self):
        self.__cache = {}

    def __getLunarLeapYear(self, year):
        """
        判斷農曆年閏月數
        @param {Number} year 農曆年
        return 閏月數（月份從1開始）
        """
        yearData = self.__lunarInfo[year - self.__minYear]
        return yearData[0]

    def __getLunarYearDays(self, year):
        """
        獲取農曆年份一年的每月的天數及一年的總天數
        @param {Number} year 農曆年
        """
        yearData = self.__lunarInfo[year - self.__minYear]
        leapMonth = yearData[0]
        monthData = yearData[3]

        monthDataArr = []
        for i in range(15, -1, -1):
            monthDataArr.append((monthData & (1 << i)) >> i)

        numMonthsInYear = 13 if leapMonth else 12
        yearDays = 0
        monthDays = []
        for i in range(numMonthsInYear):
            if monthDataArr[i] == 0:
                yearDays += 29
                monthDays.append(29)
            else:
                yearDays += 30
                monthDays.append(30)

        return {
            'yearDays': yearDays,
            'monthDays': monthDays
        }

    def __getLunarDateByBetween(self, year, between):
        """
        通過間隔天數查找農曆日期
        @param {Number} year,between 農曆年，間隔天數
        """
        lunarYearDays = self.__getLunarYearDays(year)
        end = between if between > 0 else lunarYearDays['yearDays'] + between
        monthDays = lunarYearDays['monthDays']
        tempDays = 0
        month = 0
        for i in range(len(monthDays)):
            tempDays += monthDays[i]
            if tempDays > end:
                month = i
                tempDays = tempDays - monthDays[i]
                break

        return [year, month, end - tempDays + 1]

    def __getLunarByBetween(self, year, month, day):
        """
        根據距離正月初一的天數計算農曆日期
        @param {Number} year 公曆年，月，日
        """
        yearData = self.__lunarInfo[year - self.__minYear]
        zenMonth = yearData[1]
        zenDay = yearData[2]
        between = self.__getDaysBetweenSolar(year, zenMonth - 1, zenDay,
                                             year, month, day)
        if between == 0:
            return [year, 0, 1]
        else:
            lunarYear = year if between > 0 else year - 1
            return self.__getLunarDateByBetween(lunarYear, between)

    def __getDaysBetweenSolar(self, year, month, day, year1, month1, day1):
        """
        兩個公曆日期之間的天數
        """
        # https://stackoverflow.com/a/151211
        d0 = datetime.date(year, month + 1, day)
        d1 = datetime.date(year1, month1 + 1, day1)
        delta = d1 - d0
        return delta.days

    def __getDaysBetweenZheng(self, year, month, day):
        """
        計算農曆日期離正月初一有多少天
        @param {Number} year,month,day 農年，月(0-12，有閏月)，日
        """
        lunarYearDays = self.__getLunarYearDays(year)
        monthDays = lunarYearDays['monthDays']
        days = 0
        for i in range(len(monthDays)):
            if i < month:
                days += monthDays[i]
            else:
                break
        return days + day - 1

    def __getTerm(self, y, n):
        """
        某年的第n個節氣為幾日
        31556925974.7為地球公轉週期，是毫秒
        1890年的正小寒點：01-05 16:02:31，1890年為基準點
        @param {Number} y 公曆年
        @param {Number} n 第幾個節氣，從0小寒起算
        由於農曆24節氣交節時刻採用近似算法，可能存在少量誤差(30分鐘內)
        """
        offsetms = 31556925974.7 * (y - 1890) + self.__termInfo[n] * 60000
        offDate = datetime.datetime(
            1890, 1, 5, 16, 2, 31,
            tzinfo=datetime.timezone.utc
        ) + datetime.timedelta(milliseconds=offsetms)
        return offDate.day

    def __getYearTerm(self, year):
        """
        獲取公曆年一年的二十四節氣
        返回key:日期，value:節氣中文名
        """
        res = {}
        month = 0
        for i in range(24):
            day = self.__getTerm(year, i)
            if i % 2 == 0:
                month += 1
                res[self.__formatDayD4(month - 1, day)] = self.__solarTerm[i]
        return res

    def __getYearZodiac(self, year):
        """
        獲取生肖
        @param {Number} year 干支所在年（默認以立春前的公曆年作為基數）
        """
        num = year - 1890 + 25  # 參考干支紀年的計算，生肖對應地支
        return self.__zodiac[num % 12]

    def __cyclical(self, num):
        """
        計算天干地支
        @param {Number} num 60進制中的位置(把60個天干地支，當成一個60進制的數)
        """
        return (
            self.__heavenlyStems[num % 10] +
            self.__earthlyBranches[num % 12]
        )

    def __getLunarYearName(self, year, offset=0):
        """
        獲取干支紀年
        @param {Number} year 干支所在年
        @param {Number} offset 偏移量，默認為0，便於查詢一個年跨兩個干支紀年（以立春為分界線）
        """
        # 1890年1月小寒（小寒一般是1月5或6日）以前為己丑年，在60進制中排25
        return self.__cyclical(year - 1890 + 25 + offset)

    def __getLunarMonthName(self, year, month, offset=0):
        """
        獲取干支紀月
        @param {Number} year,month 公曆年，干支所在月
        @param {Number} offset 偏移量，默認為0，便於查詢一個月跨兩個干支紀月（有立春的2月）
        """
        # 1890年1月小寒以前為丙子月，在60進制中排12
        return self.__cyclical((year - 1890) * 12 + month + 12 + offset)

    def __getLunarDayName(self, year, month, day):
        """
        獲取干支紀日
        @param {Number} year,month,day 公曆年，月，日
        """
        # 當日與189​​0/1/1 相差天數
        # 1890/1/1與1970/1/1 相差29219日, 1890/1/1 日柱為壬午日(60進制18)
        dayCyclical = (
            datetime.date(year, month + 1, day) +
            datetime.timedelta(days=29219+18) -
            datetime.date(1970, 1, 1)
        )

        return self.__cyclical(dayCyclical.days)

    def __getSolarMonthDays(self, year, month):
        """
        獲取公曆月份的天數
        @param {Number} year 公曆年
        @param {Number} month 公曆月
        """
        monthDays = [31, 29 if self.__isLeapYear(year) else 28,
                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        return monthDays[month]

    def __isLeapYear(self, year):
        """
        判斷公曆年是否是閏年
        @param {Number} year 公曆年
        """
        return (year % 4 == 0 and year % 100 != 0) or year % 400 == 0

    def __formatDate(self, year=None, month=None, day=None, _minYear=None):
        """
        統一日期輸入參數（輸入月份從1開始，內部月份統一從0開始）
        """
        now = datetime.datetime.now()
        year = int(year) if year is not None else now.year
        month = int(month) - 1 if month is not None else now.month - 1
        day = int(day) if day is not None else now.day
        if year < (_minYear if _minYear is not None
                   else self.__minYear + 1) or year > self.__maxYear:
            return {
                'error': 100,
                'msg': 'Year out of range'
            }
        return {
            'year': year,
            'month': month,
            'day': day
        }

    def lunarToSolar(self, _year, _month, _day):
        """
        將農曆轉換為公曆
        @param {Number} year,month,day 農曆年，月(1-13，有閏月)，日
        year: Gregorian year
        """
        inputDate = self.__formatDate(_year, _month, _day)
        try:
            inputDate['error']
        except KeyError:
            pass
        else:
            return inputDate
        year = inputDate['year']
        month = inputDate['month']
        day = inputDate['day']

        between = self.__getDaysBetweenZheng(year, month, day)  # 離正月初一的天數
        yearData = self.__lunarInfo[year - self.__minYear]
        zenMonth = yearData[1]
        zenDay = yearData[2]

        offDate = (
            datetime.date(year, zenMonth, zenDay) +
            datetime.timedelta(days=between)
        )
        return {
            'year': offDate.year,
            'month': offDate.month,
            'day': offDate.day
        }

    def solarToLunar(self, _year, _month, _day):
        """
        Converts Gregorian date to lunar calendar.
        _year: integer between 1891 and 2100 inclusive.
        _month, _day: integer, 1-indexed.
        """
        inputDate = self.__formatDate(_year, _month, _day, self.__minYear)
        try:
            inputDate['error']
        except KeyError:
            pass
        else:
            return inputDate

        year = inputDate['year']
        month = inputDate['month']
        day = inputDate['day']

        try:
            termList = self.__cache[year]  # 二十四節氣
        except KeyError:
            self.__cache[year] = self.__getYearTerm(year)
            termList = self.__cache[year]

        term2 = [k for (k, v) in termList.items() if v == '立春'][0]
        term2 = int(term2[-1])

        firstTerm = self.__getTerm(year, month * 2)
        GanZhiYear = (
            year + 1 if month > 1 or month == 1 and day >= term2
            else year
        )
        GanZhiMonth = month + 1 if day >= firstTerm else month

        lunarDate = self.__getLunarByBetween(year, month, day)
        lunarLeapMonth = self.__getLunarLeapYear(lunarDate[0])

        if lunarLeapMonth > 0 and lunarLeapMonth == lunarDate[1]:
            lunarMonthName = '閏' + self.__monthCn[lunarDate[1] - 1] + '月'
        elif lunarLeapMonth > 0 and lunarDate[1] > lunarLeapMonth:
            lunarMonthName = self.__monthCn[lunarDate[1] - 1] + '月'
        else:
            lunarMonthName = self.__monthCn[lunarDate[1]] + '月'

        try:
            term = termList[self.__formatDayD4(month, day)]
        except KeyError:
            term = None
        return {
            'zodiac': self.__getYearZodiac(GanZhiYear),
            'GanZhiYear': self.__getLunarYearName(GanZhiYear),
            'GanZhiMonth': self.__getLunarMonthName(year, GanZhiMonth),
            'GanZhiDay': self.__getLunarDayName(year, month, day),
            'term': term,
            'lunarYear': lunarDate[0],
            'lunarMonth': lunarDate[1] + 1,
            'lunarDay': lunarDate[2],
            'lunarMonthName': lunarMonthName,
            'lunarDayName': self.__dateCn[lunarDate[2] - 1],
            'lunarLeapMonth': lunarLeapMonth
        }
