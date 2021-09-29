# bot pour tps
# by SP

"""
fonctionnalités à terme :

* affichage des cours de la journée
  > chargement automatique d'un fichier qui contient l'emploi du temps
  > au début on pourra se contenter de déposer les fichiers à la main, mais à terme il faudrait récup le fichier automatiquement

"""

import os
import time

import discord
from discord.ext import commands
from dotenv import load_dotenv
import urllib.request
import random


def convTime(t):
    """
    :param t: formatted time : "yyyyMMddTHHmmssZ"
    :return: (year,month,day,hour,minute,second) all as integers
    """
    return int(t[0:4]), int(t[4:6]), int(t[6:8]), int(t[9:11]), int(t[11:13]), int(t[13:15])


def getCal(url="https://monemploidutemps.unistra.fr/api/calendar/0ccba05c-6cbf-4108-90e2-865ea0ddd0c7/export"):
    # https://monemploidutemps.unistra.fr/config

    file = urllib.request.urlopen(url)
    lines = [line.decode("utf-8")[:-2] for line in file]

    # print(len(lines))
    n = len(lines)

    events = []

    i = 0
    while i < n:
        line = lines[i]
        if line == "BEGIN:VEVENT":
            evt = []
            i += 1
            while lines[i] != "END:VEVENT":
                evt.append(lines[i])
                i += 1
            events.append(evt)
        i += 1

    dictEvt = {}
    """
        structure :
        (day,month): {
            (heure_d,minute_d,heure_f,minute_f): {
                "debut": (hh,mm),
                "fin": (hh,mm),
                "creneau": "8h30 - 10h30",
                "salle": salle,
                "description": description,
                "resume": résumé
            },
            ...
        },
        ...

    """

    for evt in events:
        # print(evt)
        description = ""
        debut = ""
        fin = ""
        location = ""
        summary = ""
        day = ""
        dtstart = ""
        dtend = ""
        # 2021 10 20 T 17 30 00 Z # format date
        for l in evt:
            if l[:12] == "DESCRIPTION:":
                description = l[12:]
            elif l[:6] == "DTEND:":
                dtend = convTime(l[6:])  # (year,month,day,hour,minute,second)
            elif l[:8] == "DTSTART:":
                dtstart = convTime(l[8:])
            elif l[:9] == "LOCATION:":
                location = l[9:]
            elif l[:8] == "SUMMARY:":
                summary = l[8:]
        # print(f"{description = }\n{fin = }\n{debut = }\n{location = }\n{summary = }\n{day = }")

        cours = dict()
        cle = (dtstart[3] + 2, dtstart[4], dtend[3] + 2, dtend[4])
        cours["debut"] = (dtstart[3] + 2, dtstart[4])
        cours["fin"] = (dtend[3] + 2, dtend[4])
        cours["creneau"] = str(dtstart[3] + 2) + "h" + str(dtstart[4]) + "0" * (2 - len(str(dtstart[4]))) + " - " + str(
            dtend[3] + 2) + "h" + str(dtend[4]) + "0" * (2 - len(str(dtend[4])))
        cours["resume"] = summary
        cours["description"] = description
        cours["salle"] = location

        day = (dtstart[2], dtstart[1])
        if day in dictEvt.keys():
            dictEvt[day][cle] = cours.copy()
        else:
            dictEvt[day] = {}
            dictEvt[day][cle] = cours.copy()

    return dictEvt


def getToday(cal):
    today = time.localtime()
    day = (today[2], today[1])
    if day in cal.keys():
        return cal[day]
    else:
        return dict()


def getDay(cal, j, m):
    if (j, m) in cal.keys():
        return cal[(j, m)]
    else:
        return dict()


def printDict(d, depth=0):
    for key in d.keys():
        e = d[key]
        if type(e) == dict:
            print("    " * depth + "{} : ".format(key))
            printDict(e, depth + 1)
        else:
            print("    " * depth + "{} : {}".format(key, e))


def relatif(hd, md, hf, mf, h, m):
    """
    :param hd: heure de début
    :param md: minute de début
    :param hf: heure de fin
    :param mf: minute de fin
    :param h: heure à tester
    :param m: minute à tester
    :return: 0 si l'heure à tester est avant le début
             1 si l'heure est pendant le créneau
             2 si l'heure est après
    on suppose bien sûr que toutes ces heures font références à la même journée
    """
    if h < hd:
        return 0
    if h > hf:
        return 2
    else:
        if h == hd and m < md:
            return 0
        elif h == hf and m > mf:
            return 2
    return 1

def est_avant(h1,m1,h2,m2):
    """
    :param h1: premiere heure
    :param m1:
    :param h2: deuxième heure
    :param t2:
    :return: true si la premire heure est avant la deuxieme
             false sinon
    """
    return (h1 < h2) or (h1 == h2 and m1 <= m2)


def until(h1, m1, h2, m2):
    """
    :param h1: heure, minute 1
    :param m1:
    :param h2: heure minute 2
    :param m2:
    :return: le nombre de minutes pour passer de l'heure 1 à l'heure 2
    on suppose donc que l'heure 1 est AVANT l'heure 2
    """
    return 60 * (h2 - h1) + m2 - m1


def code(t):
    return "```" + t + "```"


def est_bissextile(a):
    if a % 400 == 0: return True
    if a % 100 == 0: return False
    if a % 4 == 0: return True


def demain(j, m, a=-1):
    """
    :param j: jour du mois
    :param m: le mois
    :param a: l'année, par défaut -1 = on s'en fiche, et on considère que l'année n'est pas bissextile
    :return: le jour après le jour envoyé en argument, sous la forme (j,m) si a n'est pas passée,
                                                                  ou (j,m,a) si a est passée
    """
    if j == 31 and m == 12:  # cas part: fin d'année
        if a == -1:
            return 1, 1
        else:
            return 1, 1, a + 1
    if j == 28 and m == 2:  # cas part: février
        if a == -1:
            return 1, 3  # on ignore l'année, on considère qu'elle n'est pas bissextile (3 chances sur 4 ez)
        else:
            if est_bissextile(a):
                return 29, 2, a
            else:
                return 1, 3, a
    elif j == 29 and m == 2:  # cas part: février, part 2
        if a == -1:
            return 1, 3
        else:
            return 1, 3, a
    elif (j == 30 and m in (4, 6, 9, 11)) or j == 31:  # fins de mois
        if a == -1:
            return 1, m + 1
        else:
            return 1, m + 1, a
    else:
        if a == -1:
            return j + 1, m
        else:
            return j + 1, m, a


def prep_dict(d, depth=0, ignoredkeys=None):
    if ignoredkeys is None:
        ignoredkeys = ["debut", "fin", "description"]
    ret = ""
    for key in d.keys():
        if key not in ignoredkeys:
            e = d[key]
            if type(e) == dict:
                ret += ("   " * depth + "{} : \n".format(key))
                ret += (prep_dict(e, depth + 1)) + "\n"
            else:
                ret += ("   " * depth + "{} : {}\n".format(key, e))
    return ret


def randomColor():
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return r, g, b


def run():
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')

    client = commands.Bot(command_prefix="!")
    cal = getCal(url="https://monemploidutemps.unistra.fr/api/calendar/0ccba05c-6cbf-4108-90e2-865ea0ddd0c7/export")

    @client.event
    async def on_ready():
        print(f'{client.user} has connected to Discord')
        # activity = discord.CustomActivity(name="TEST2")
        # await client.change_presence(activity=activity)
        # ne fonctionne pas, peut-être que ça n'est pas possible pour un bot :(

    async def sendCours(ctx,cours):
        # printDict(cours)
        creneau = cours["creneau"]
        salle = cours["salle"]
        resume = cours["resume"]
        embed = discord.Embed(title=resume, description=creneau + "\n" + salle, color=discord.Color.from_rgb(*randomColor()))
        await ctx.send(embed=embed)

    async def sendListeCours(ctx,liste):
        """
        :param ctx: contexte au sens de discord = le channel où le message sera envoyé
        :param liste: liste de dictionnaires de cours
        :return: None
        """
        # tri
        cp = liste.copy()
        liste_trie = []
        # print(cp)
        while cp: # tant que cp n'est pas vide
            premier_i = 0
            premier_h = cp[0]["debut"]
            for i in range(1,len(cp)):
                if est_avant(*cp[i]["debut"], *premier_h):
                    premier_i = i
                    premier_h = cp[i]["debut"]
            liste_trie.append(cp.pop(premier_i))

        for cours in liste_trie:
            await sendCours(ctx, cours)


    @client.command(name="test")
    async def test(ctx):
        cours_today = getToday(cal)
        key = list((cours_today.keys()))[0]
        cours = cours_today[key]
        await sendCours(ctx, cours)

    @client.command(name="next")
    async def nextCours(ctx):
        date = time.localtime()  # year, month, day, hours, minutes, seconds, ...
        today = [date[2], date[1]]  # on ignore l'année, penser à mettre un check pour passer à 2022 quand meme
        h, m = (date[3], date[4])  # h_debut,h,h_fin ...
        today_cours = getToday(cal)
        not_begun = []  # liste des cours pas encore commencés, sous forme ( key , temps avant début en minutes )
        en_cours = []  # liste des cours déjà commencés, sous la forme d'une liste de key
        for hd, md, hf, mf in today_cours.keys():
            rel = relatif(hd, md, hf, mf, h, m)
            if rel == 0:  # le cours n'a pas commencé
                dt = until(h, m, hd, md)
                not_begun.append([(hd, md, hf, mf), dt])
            elif rel == 1:  # le cours a déjà commencé
                en_cours.append((hd, md, hf, mf))
            else:  # le cours est déjà fini
                pass  # fonc on ignore
        if len(en_cours) != 0:  # ie il y a des cours actuellement
            if len(en_cours) == 1:
                await ctx.send("Ce cours est en cours :")
                await sendCours(ctx, today_cours[en_cours[0]])
            else:
                await ctx.send("Ces cours sont en cours :")
                for key in en_cours:
                    await sendCours(ctx, today_cours[key])
        if len(not_begun) != 0:  # il reste des cours aujourd'hui qui n'ont pas commencés
            await ctx.send("Le prochain cours est :")
            plusprocheindex = 0
            plusproche = not_begun[0][1]
            for i, e in enumerate(not_begun):
                if e[1] < plusproche:
                    plusproche = e[1]
                    plusprocheindex = i
            await sendCours(ctx, today_cours[not_begun[plusprocheindex][0]])
        else:  # plus aucun cours aujourd'hui, on va chercher demain ou plus loin encore
            await ctx.send("Plus de cours aujourd'hui !")
            nextday = demain(*today)
            keys = cal.keys()
            limite = 100
            i = 0
            while not (nextday in keys) and i < limite:
                nextday = demain(*nextday)
                i += 1
            if i == 100:
                await ctx.send("Aucun cours trouvé dans les 100 prochains jours :(")
            else:
                await ctx.send("Le prochain cours sera le {}/{} :\n".format(*nextday))
                cours_de_ce_jour = getDay(cal, *nextday)
                premier_cours = (24, 60)
                premier_cours_key = ()
                for hd, md, hf, mf in cours_de_ce_jour.keys():
                    if hd < premier_cours[0] or (hd == premier_cours[0] and md < premier_cours[1]):
                        premier_cours = (hd, md)
                        premier_cours_key = (hd, md, hf, mf)
                await sendCours(ctx, cours_de_ce_jour[premier_cours_key])


    @client.command(name="cours")
    async def cours(ctx, date=None):
        if date is None:
            jour = getToday(cal)
            # await message.channel.send("```" + prep_dict(jour) + "```")
            await ctx.send("Cours d'aujourd'hui :\n")
            # to_send += code(prep_dict(jour)) + "\n"
            # for cours in jour.values():
            #     await sendCours(ctx, cours)
            await sendListeCours(ctx, list(jour.values()))
        else:
            date = date.split("/")
            if len(date) != 2:
                await ctx.send("Utilisation : `!date jj/mm`")
                return
            try:
                month = int(date[1])
                day = int(date[0])
            except ValueError:
                await ctx.send("Utilisation : `!date jj/mm`")
                return
            if (day, month) in cal.keys():
                await ctx.send("Cours du {}/{}\n".format(date[0], date[1]))
                # to_send += code(prep_dict(cal[(day, month)])) + "\n"
                # jour = cal[(day, month)]
                # for cours in jour.values():
                #     await sendCours(ctx, cours)
                await sendListeCours(ctx, list(cal[(day, month)].values()))
            else:
                await ctx.send("Pas de cours le {}/{}\n".format(date[0], date[1]))

    @client.command(name="demain")
    async def coursDemain(ctx):
        date = time.localtime()  # year, month, day, hours, minutes, seconds, ...
        today = [date[2], date[1]]
        dem = demain(*today)
        if dem in cal.keys():
            await ctx.send("Cours de demain : ({}/{})".format(*dem))
            # for cours in cal[dem].values():
            #     await sendCours(ctx, cours)
            await sendListeCours(ctx, list(cal[dem].values()))
        else:
            await ctx.send("Pas de cours demain ! ({}/{})".format(*dem))

    client.run(TOKEN)

