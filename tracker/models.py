#
# tracker/models.py
# Copyright (C) 2016 Alexei Frolov
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

# Create your models here.

class RSAccount(models.Model):
    username = models.CharField(max_length=12)

    def __str__(self):
        return self.username


class DataPoint(models.Model):
    id = models.BigAutoField(primary_key=True)
    rsaccount = models.ForeignKey(RSAccount, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return 'Datapoint: %s at %s' % (str(self.rsaccount), str(self.time))


class Skill(models.Model):
    skill_id = models.PositiveSmallIntegerField(primary_key=True)
    skillname = models.CharField(max_length=16)

    def __str__(self):
        return '%d %s' % (self.skill_id, self.skillname)


class SkillLevel(models.Model):
    id = models.BigAutoField(primary_key=True)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    datapoint = models.ForeignKey(DataPoint, on_delete=models.CASCADE)
    experience = models.BigIntegerField()
    rank = models.IntegerField()

    class Meta:
        unique_together = (( 'skill', 'datapoint' ))

    def __str__(self):
        return '%d: %d, %d' % (self.skill_id, self.experience, self.rank)
