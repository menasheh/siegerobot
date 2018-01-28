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

str1 = """🏘Houses   

Level            482
People    9640/9640👥
           +482👥/day
          -4820🍖/day

Farm      +1810🍖/day
Storage        4740👥

Upgrade   
         23377200💰⛔️
         11688600🌲​✅
         11688600⛏​✅"""


print(re.findall(reg, str1))
print_matches(re.search(reg, str1))


"""
⚔ The battle was all night and your warriors won the battle. But your soldiers suffered heavy losses. 6699⚔ returned home. Your treasury is replenished 17211893💰.

‼️Your domain attacked! [🌲]Dimonstr approaches the border! Your whole ⚔Army will be sent to the defense!

‼️The battle with Yamaha complete. Congratulations, Liquid! Your army won. The winners 16394⚔ of 16400⚔ proudly return home. Your reward is 1635550💰, and 242🗺 joined to your domain.
‼️The battle with [🌋]Botolengket complete. Congratulations, Liquid! Your army won. The winners 16400⚔ without a loss proudly return home. Your reward is 3030414💰, and 92🗺 joined to your domain.

⚔ The shop is closed because war in progress...
"""