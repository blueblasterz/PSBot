# bot pour tps
# by SP
<<<<<<< HEAD

=======
>>>>>>> 877d4373844f133806ba2e3adef66742522bb340

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
        to_send = ""
        if len(en_cours) != 0:  # ie il y a des cours actuellement
            if len(en_cours) == 1:
                to_send += "Ce cours est en cours :\n"
                to_send += code(prep_dict(today_cours[en_cours[0]])) + "\n"
            else:
                to_send += "Ces cours sont en cours :\n"
                for key in en_cours:
                    to_send += code(prep_dict(today_cours[key])) + "\n"
        if len(not_begun) != 0:  # il reste des cours aujourd'hui qui n'ont pas commencés
            to_send += "Le prochain cours est :\n"
            plusprocheindex = 0
            plusproche = not_begun[0][1]
            for i, e in enumerate(not_begun):
                if e[1] < plusproche:
                    plusproche = e[1]
                    plusprocheindex = i
            to_send += code(prep_dict(today_cours[not_begun[plusprocheindex][0]])) + "\n"
        else:  # plus aucun cours aujourd'hui, on va chercher demain ou plus loin encore
            to_send += "Plus de cours aujourd'hui !\n"
            nextday = demain(*today)
            keys = cal.keys()
            limite = 100
            i = 0
            while not (nextday in keys) and i < limite:
                nextday = demain(*nextday)
                i += 1
            if i == 100:
                to_send += "Aucun cours trouvé dans les 100 prochains jours :(\n"
            else:
                to_send += "Le prochain cours sera le {}/{} :\n".format(*nextday)
                cours_de_ce_jour = getDay(cal, *nextday)
                premier_cours = (24, 60)
                premier_cours_key = ()
                for hd, md, hf, mf in cours_de_ce_jour.keys():
                    if hd < premier_cours[0] or (hd == premier_cours[0] and md < premier_cours[1]):
                        premier_cours = (hd, md)
                        premier_cours_key = (hd, md, hf, mf)
                to_send += code(prep_dict(cours_de_ce_jour[premier_cours_key])) + "\n"
        await ctx.send(to_send)

    @client.command(name="oui")
    async def ping(ctx):
        ctx.send("non")

    @client.command(name="cours")
    async def cours(ctx, date=None):
        if date == None:
            jour = getToday(cal)
            # await message.channel.send("```" + prep_dict(jour) + "```")
            to_send = "Cours d'aujourd'hui :\n"
            to_send += code(prep_dict(jour)) + "\n"
            await ctx.send(to_send)
        else:
            date = date.split("/")
            if len(date) != 2:
                to_send = "Utilisation : `!date jj/mm`"
            else:
                try:
                    month = int(date[1])
                    day = int(date[0])
                except ValueError:
                    to_send = "Utilisation : `!date jj/mm`"
                    await message.channel.send(to_send)
                    return
                if (day, month) in cal.keys():
                    to_send = "Cours du {}/{}\n".format(date[0], date[1])
                    to_send += code(prep_dict(cal[(day, month)])) + "\n"
                else:
                    to_send = "Pas de cours le {}/{}\n".format(date[0], date[1])
            await ctx.send(to_send)

    @client.command(name="demain")
    async def coursDemain(ctx):
        date = time.localtime()  # year, month, day, hours, minutes, seconds, ...
        today = [date[2], date[1]]
        dem = demain(*today)
        if dem in cal.keys():
            to_send = "Cours de demain : ({}/{})\n".format(*dem)
            to_send += code(prep_dict(cal[dem])) + "\n"
        else:
            to_send = "Pas de cours demain ! ({}/{})\n".format(*dem)
        await ctx.send(to_send)

    client.run(TOKEN)

