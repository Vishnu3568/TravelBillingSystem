import re

class NumberToWordsUtil:
    tens_names = [
        "", " Ten", " Twenty", " Thirty", " Forty", " Fifty", " Sixty", " Seventy", " Eighty", " Ninety"
    ]

    num_names = [
        "", " One", " Two", " Three", " Four", " Five", " Six", " Seven", " Eight", " Nine", " Ten",
        " Eleven", " Twelve", " Thirteen", " Fourteen", " Fifteen", " Sixteen", " Seventeen", " Eighteen", " Nineteen"
    ]

    @classmethod
    def _convert_less_than_one_thousand(cls, number: int) -> str:
        if number % 100 < 20:
            so_far = cls.num_names[number % 100]
            number //= 100
        else:
            so_far = cls.num_names[number % 10]
            number //= 10
            so_far = cls.tens_names[number % 10] + so_far
            number //= 10
            
        if number == 0:
            return so_far
        return cls.num_names[number] + " Hundred" + so_far

    @classmethod
    def convert(cls, number: int) -> str:
        if number == 0:
            return "Zero"

        snumber = str(number).zfill(12)

        billions = int(snumber[0:3])
        millions = int(snumber[3:6])
        hundred_thousands = int(snumber[6:9])
        thousands = int(snumber[9:12])

        result = ""

        if billions > 0:
            result += cls._convert_less_than_one_thousand(billions) + " Billion "

        if millions > 0:
            result += cls._convert_less_than_one_thousand(millions) + " Million "

        if hundred_thousands > 0:
            if hundred_thousands == 1:
                result += "One Thousand "
            else:
                result += cls._convert_less_than_one_thousand(hundred_thousands) + " Thousand "

        result += cls._convert_less_than_one_thousand(thousands)

        result = re.sub(r'^\s+', '', result)
        result = re.sub(r'\s{2,}', ' ', result)
        return result.strip()

    @classmethod
    def convert_to_rupees(cls, amount: float) -> str:
        rupees = int(amount)
        paise = int(round((amount - rupees) * 100))

        result = cls.convert(rupees) + " Rupees"
        if paise > 0:
            result += " and " + cls.convert(paise) + " Paise"
        return result + " Only"
