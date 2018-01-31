import re


def print_matches(m):
    if m is not None:
        for i in range(0, m.lastindex + 1):
            if m.group(i) is not None:
                print(str(i) + ": " + m.group(i))

    else:
        print("No Match!")


reg = re.compile(r'with (?:\[(\W)])?([\w ]+) complete.+winners (\d+)⚔ (?:of (\d+)⚔)?.+(?:reward is (\d+)💰)(?:\.|, and (\d+)🗺 joined)')
# [⛏,🌲]

str1 = """️Your domain attacked! []Darksoul approaches the border! Your whole Army will be sent to the defense!
ERROR: unknown message type!!!
The battle with []Darksoul complete. Unfortunately, Liquid, your army lose. Only 3 of 9392 returned from the battlefield... You lose 4181089, and 713 joined to []Darksoul."""

m = re.findall(reg, str1)

print(m)
print_matches(re.search(reg, str1))


"""
⚔ The battle was all night and your warriors won the battle. But your soldiers suffered heavy losses. 6699⚔ returned home. Your treasury is replenished 17211893💰.

‼️Your domain attacked! [🌲]Dimonstr approaches the border! Your whole ⚔Army will be sent to the defense!

‼️The battle with [🌲]Darksoul complete. Unfortunately, Liquid, your army lose. Only 3⚔ of 9392⚔ returned from the battlefield... You lose 4181089💰, and 713🗺 joined to [🌲]Darksoul.

‼️The battle with Yamaha complete. Congratulations, Liquid! Your army won. The winners 16394⚔ of 16400⚔ proudly return home. Your reward is 1635550💰, and 242🗺 joined to your domain.
‼️The battle with [🌋]Botolengket elephant complete. Congratulations, Liquid! Your army won. The winners 16400⚔ without a loss proudly return home. Your reward is 3030414💰, and 92🗺 joined to your domain.
‼️The battle with [🔥]Евген complete. Congratulations, Liquid! Your army won. The winners 9391⚔ of 16400⚔ proudly return home. Your reward is 2575518💰.

⚔ The shop is closed because war in progress...
"""

