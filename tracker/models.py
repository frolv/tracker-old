#
# tracker/models.py
# Copyright (C) 2016-2017 Alexei Frolov
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

from django.db import models

class RSAccount(models.Model):
    """
    A tracked OSRS account, with name and ID.
    """

    username = models.CharField(max_length=12, db_index=True)
    total_exp = models.BigIntegerField(db_index=True)

    def __str__(self):
        return self.username


class DataPoint(models.Model):
    """
    A data point for a specific account at a given time.
    """

    id = models.BigAutoField(primary_key=True)
    rsaccount = models.ForeignKey(RSAccount, on_delete=models.CASCADE,
                                  db_index=True)
    time = models.DateTimeField(auto_now_add=True, editable=False,
                                db_index=True)

    def __str__(self):
        return 'Datapoint: %s at %s' % (str(self.rsaccount), str(self.time))


class Skill(models.Model):
    """
    A skill in OSRS.
    """

    skill_id = models.PositiveSmallIntegerField(primary_key=True)
    skillname = models.CharField(max_length=16)

    # Skill IDs for QHA and Original QHA
    QHA_ID = 99
    ORIG_QHA_ID = 100

    def __str__(self):
        return '%d %s' % (self.skill_id, self.skillname)


class SkillLevel(models.Model):
    """
    Experience in rank in a certain skilll at a certain datapoint.
    """

    id = models.BigAutoField(primary_key=True)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    datapoint = models.ForeignKey(DataPoint, on_delete=models.CASCADE,
                                  db_index=True)
    experience = models.BigIntegerField()
    rank = models.IntegerField()
    current_hours = models.FloatField()
    original_hours = models.FloatField()

    class Meta:
        unique_together = (( 'skill', 'datapoint' ))

    def __str__(self):
        return '%s: %d, %d' % (self.skill.skillname, self.experience, self.rank)


class Current(models.Model):
    """
    Current experience gain in a skill for a player within a time period: day,
    week, month or year. Stores first and last datapoints within the period and
    the experience gained.
    """

    DAY = 'D'
    WEEK = 'W'
    MONTH = 'M'
    YEAR = 'Y'
    PERIOD_CHOICES = (
        (DAY, 'Day'),
        (WEEK, 'Week'),
        (MONTH, 'Month'),
        (YEAR, 'Year'),
    )

    rsaccount = models.ForeignKey(RSAccount, on_delete=models.CASCADE,
                                  db_index=True)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    start = models.ForeignKey(DataPoint, on_delete=models.CASCADE,
                              db_index=True, related_name='+')
    end = models.ForeignKey(DataPoint, on_delete=models.CASCADE,
                            db_index=True, related_name='+')
    experience = models.BigIntegerField(db_index=True)
    period = models.CharField(max_length=1, choices=PERIOD_CHOICES, db_index=True)
    hours = models.FloatField()

    class Meta:
        unique_together = (( 'rsaccount', 'skill', 'period' ))

    def __str__(self):
        return '%s: %d xp %s in %s at %s' % (self.rsaccount.username,
                                             self.experience, self.period,
                                             self.skill.skillname,
                                             self.start.time)

    def str_to_period(s):
        periods = {
            'day': Current.DAY,
            'week': Current.WEEK,
            'month': Current.MONTH,
            'year': Current.YEAR,
        }
        return periods[s]


class Record(models.Model):
    """
    Record experience gained by a player in a skill within a certain period.
    Identical to Current, with addition of FIVE_MIN period; see it for details.
    """

    FIVE_MIN = '5'
    DAY = 'D'
    WEEK = 'W'
    MONTH = 'M'
    YEAR = 'Y'
    PERIOD_CHOICES = (
        (FIVE_MIN, 'Five minute'),
        (DAY, 'Day'),
        (WEEK, 'Week'),
        (MONTH, 'Month'),
        (YEAR, 'Year'),
    )

    rsaccount = models.ForeignKey(RSAccount, on_delete=models.CASCADE,
                                  db_index=True)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    start = models.ForeignKey(DataPoint, on_delete=models.CASCADE,
                              db_index=True, related_name='+')
    end = models.ForeignKey(DataPoint, on_delete=models.CASCADE,
                            db_index=True, related_name='+')
    experience = models.BigIntegerField(db_index=True)
    period = models.CharField(max_length=1, choices=PERIOD_CHOICES, db_index=True)
    hours = models.FloatField()

    class Meta:
        unique_together = (( 'rsaccount', 'skill', 'period' ))

    def __str__(self):
        return '%s: %d xp %s in %s at %s' % (self.rsaccount.username,
                                             self.experience, self.period,
                                             self.skill.skillname,
                                             self.start.time)

    def str_to_period(s):
        periods = {
            'day': Record.DAY,
            'week': Record.WEEK,
            'month': Record.MONTH,
            'year': Record.YEAR,
            'fivemin': Record.FIVE_MIN,
        }
        return periods[s]


class SkillRate(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, db_index=True)
    start_exp = models.IntegerField()
    rate = models.IntegerField()
    explanation = models.CharField(max_length=128, default='')

    class Meta:
        unique_together = (( 'skill', 'start_exp' ))

    def __str__(self):
        return '%s: %d exp/h at %d exp' % (self.skill.skillname,
                                           self.rate, self.start_exp)


class TimePlayed(models.Model):
    rsaccount = models.ForeignKey(RSAccount, on_delete=models.CASCADE,
                                  db_index=True)
    hours = models.FloatField(db_index=True)

    def __str__(self):
        return '%s: %g hours' % (self.rsaccount.username, self.hours)


class TimePlayedRank(models.Model):
    datapoint = models.ForeignKey(DataPoint, on_delete=models.CASCADE,
                                  db_index=True)
    rank = models.IntegerField()

    def __str__(self):
        return 'datapoint %d: rank %d' % (self.datapoint_id, self.rank)
