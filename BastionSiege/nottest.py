import re

"""
m = re.search(r'(^Your ⚔Army).+([0-9]{1,2})', "Your ⚔Army has not yet recovered from the last battle."
                           1                   " Wait another 2 min.")
"""

def print_matches(m):
    if m is not None:
        for i in range(1, m.lastindex):
            if m.group(i) is not None:
                print(str(i) + ": " + m.group(i))

    else:
        print("No Match!")


reg = re.compile(r'(-?\d+)')
# [⛏,🌲]

str1 = """⚔Trebuchet

Level            112
Workers       20/20👥

Hire           1💰/1👥

Atk. bonus      +56⚔
Attack         2240⚔

Gold       31800184💰
People         9660👥

Upgrade   
         51528000💰⛔️
          6441000🌲✅
          1932300⛏✅️"""

storage_is_full = 0

reg = re.compile(r'(\d+)')
m = re.findall(reg, str1)

print(m)
print_matches(re.search(reg, str1))


"""
⚔ The battle was all night and your warriors won the battle. But your soldiers suffered heavy losses. 6699⚔ returned home. Your treasury is replenished 17211893💰.

‼️Your domain attacked! [🌲]Dimonstr approaches the border! Your whole ⚔Army will be sent to the defense!

‼️The battle with Yamaha complete. Congratulations, Liquid! Your army won. The winners 16394⚔ of 16400⚔ proudly return home. Your reward is 1635550💰, and 242🗺 joined to your domain.
‼️The battle with [🌋]Botolengket complete. Congratulations, Liquid! Your army won. The winners 16400⚔ without a loss proudly return home. Your reward is 3030414💰, and 92🗺 joined to your domain.

⚔ The shop is closed because war in progress...
"""

