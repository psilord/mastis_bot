import datetime as dt
import pytz

def compute_kilta_ordinal(ord):
	# I'm sorry, but it was easier to do this quick hack than it was
	# to figure out ~R for Kílta when there are phonological process inolved
	# I don't quite understand.
	date_ordinal = [
		'',					# 0th (Not used)
		'tëhin',			# 1st
		'timënin',			# 2nd
		'valënin',			# 3rd
		'lossënin',			# 4th
		'súlënin',			# 5th
		'nitënin',			# 6th
		'satënin',			# 7th
		'hërënin',			# 8th
		'nuëlënin',			# 9th
		'kólënin',			# 10th
		'kól-tëhin',		# 11th
		'kól-timënin',		# 12th
		'kól-valënin',		# 13th
		'kól-lossënin',		# 14th
		'kól-súlënin',		# 15th
		'kól-nitënin',		# 16th
		'kól-satënin',		# 17th
		'kól-hërënin',		# 18th
		'kól-nuëlënin',		# 19th
		'tinkólënin',		# 20th
		'tinkól-tëhin',		# 21st
		'tinkól-timënin',	# 22nd
		'tinkól-valënin',	# 23th
		'tinkól-lossënin',	# 24th
		'tinkól-súlënin',	# 25th
		'tinkól-nitënin',	# 26th
		'tinkól-satënin',	# 27th
		'tinkól-hërënin',	# 28th
		'tinkól-nuëlënin',	# 29th
		'valkólënin',		# 30th
		'valkól-tëhin',		# 31st
	]

	return date_ordinal[ord]

def compute_kilta_date():
	# Time started in this timezone and on this day.
	tz = pytz.timezone('America/Chicago')
	EPOCH = dt.datetime(2001, 9, 5, 0, 0, 0, 0, tz)
	now = dt.datetime.now(tz)
	kilta_now = now - EPOCH

	days_since_epoch = kilta_now.days
	weekday = now.timetuple().tm_wday
	month = now.timetuple().tm_mon - 1
	daynum = now.timetuple().tm_mday

	kaura = [
		'Ëssúr vë Tëka',		# January
		'Ëssúr vë Mika',		# Februrary
		'Natán vë Mata',		# March
		'Natán vë Tëka',		# April
		'Natán vë Chantëm',		# May
		'Viukkor vë Asitta',	# June
		'Viukkor vë Tëka',		# July
		'Viukkor vë Lamerëm',	# August
		'Víntán vë Mika',		# September
		'Víntán vë Tëka',		# October
		'Víntán vë Aráva',		# November
		'Ëssúr vë Kinta',		# December
	]

	au = [
		'Kolkol',	# Butterfly
		'Immira',	# Hawk
		'Nurës',	# Bee
		'Kokwara',	# Crow
		'Aunka'
	][days_since_epoch % 5]

	kiv = [
		'Rin',		# Oak
		'Ussala',	# Elm
		'Itar'		# Ash
	][days_since_epoch % 3]

	tun = [
		'Lastun',		# Monday
		'Anlastun',		# Tuesday
		'Tillastun',	# Wednesday
		'Vallastun',	# Thursday
		'Lólastun', 	# Friday
		'Nirusattun',	# Saturday
		'Sattun'		# Sunday
	][weekday]

	dayord = compute_kilta_ordinal(daynum)

	return (kaura[month], f"{dayord} tun", f"{au} {kiv} {tun}")

(month, day, aunka) = compute_kilta_date()

print(f"{month} {day} {aunka}")

