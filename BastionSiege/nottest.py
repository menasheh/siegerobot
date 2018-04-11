import re

"""
m = re.search(r'(^Your ⚔Army).+([0-9]{1,2})', "Your ⚔Army has not yet recovered from the last battle."
                           1                   " Wait another 2 min.")
"""


def print_matches(m):
    if m is not None:
        for i in range(1, m.lastindex + 7):
            if m.group(i) is not None:
                print(str(i) + ": " + m.group(i))

    else:
        print("No Match!")


reg = re.compile(r'(\d+)🎖\D+(\d+)\D+(\d+)\D+(\d+)/(\d+)\D+(\d+)/(\d+)\D+(\d+)/(\d+)\D+(\d+)/(\d+)⚔(⛔️|✅)\D+(\d+)🍖(⛔️|✅)(.+Next attack - (\d+) (min|sec)\.)?(.+Next ally attack - (\d+) (min|sec)\.)?(.+No attacks - (\d+) (min|sec)\.)?(.+Continues the battle with( alliance)? \[?(\W?)]?([\w ]+)(\nAttack: (.+)Defence: (.+))?)?', re.S)
# [⛏,🌲]

str1 = """Wins           2497🎖
Karma          3447☯
Territory    100972🗺

🏰Walls   10600/10600⚒
          1060/1060🏹

⚔Trebuchet    20/20👥

       8000/16400⚔✅
         10934537🍖✅

Next attack - 4 min.
Next ally attack - 4 min.
No attacks - 52 min.
Continues the battle with [🐰]omeone else"""

str2 = """Wins           2497🎖
Karma          3447☯
Territory    100972🗺

🏰Walls   10600/10600⚒
          1060/1060🏹

⚔Trebuchet    20/20👥

       8000/16400⚔✅
         10934537🍖✅

Next attack - 4 min.
Next ally attack - 4 min.
No attacks - 52 min.
Continues the battle with alliance [🐰]evil bunnies
Attack: First name, Second name, thirdname, etcname
Defence: Someone, Someone else"""


print(re.findall(reg, str1))
print_matches(re.search(reg, str1))

print("\n===\n")

print(re.findall(reg, str2))
print_matches(re.search(reg, str2))
