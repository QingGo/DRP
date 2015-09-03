'''A module for turning querysets into csv files or output'''
import csv
from django.db import models
import abc
from collections import OrderedDict

class CsvModel(models.Model):

  class Meta:
    abstract = True

  @abc.abstractproperty
  def values(self):
    '''Returns a dict of values suitable for use by a csv.DictWriter'''
    values = {}
    for field in self._meta.fields:
      try:
        if any(string in getattr(self, field.name) for string in (',', ' ')):
          values[field.name]='"{}"'.format(getattr(self, field.name))
        else:
          values[field.name]=getattr(self, field.name)
      except TypeError:
        values[field.name] = getattr(self, field.name)
    return values

  @abc.abstractproperty
  def expandedValues(self):
    '''Returns a dict of values suitable for use by a csv.DictWriter, including any special expanded values'''
    return self.values

class CsvQuerySet(models.query.QuerySet):
  '''This queryset permits the output of the data from a model as a csv'''

  __metaclass__ = abc.ABCMeta

  @abc.abstractproperty
  def expandedCsvHeaders(self):
    '''For some classes, like Compounds and Reactions, there needs to be the option to send additional data (descriptors)
    as part of the csv. This method permits that expansion, and defaults to return the non-expanded headers.'''
    return self.headers

  @abc.abstractproperty
  def csvHeaders(self):
    '''The basic headers to be used for the model. Note that the implementation on the CsvQuerySet class is extremely basic,
    and will fail if any field holds a relationship, and will not include automagically generated fields.'''
    return [field.name for field in self.model._meta.fields]

  def toCsv(self, writeable, expanded=False, missing="?"):#TODO:figure out most sensible default for missing values
    '''Writes the csv data to the writeable (file, or for Django a HttpResponse) object. Expanded outputs any expanded
      information that the corresponding methods provide- this requires the model being called to have a property
      'expandedValues', which should be a dictionary like object of values, using fieldNames as keys as output
      by fetchExpandedHeaders.
    '''

    if expanded:
      writer = csv.DictWriter(writeable, fieldnames=self.expandedCsvHeaders, restval=missing)
    else:
      writer = csv.DictWriter(writeable, fieldnames=self.csvHeaders, restval=missing)

    writer.writeheader()
    for item in self:
      if expanded:
        writer.writerow(item.expandedValues)
      else:
        writer.writerow(item.values)

class ArffQuerySet(models.query.QuerySet):
  '''This queryset class permits data from a model to be output as a .arff file'''

  __metaclass__ = abc.ABCMeta

  @abc.abstractproperty
  def expandedArffHeaders(self):
    '''returns expanded headers, designed to be overridden by classes that need it'''
    return self.headers

  @abc.abstractproperty
  def arffHeaders(self):
    '''the basic headers to be used for the mode. Note that this imlementation is extremely basic, though not as much so as
    the csv file query set. This will manage foreignkey relations (make sure to define __unicode__ on your models!), 
    but won't handle automagic fields or fields to many objects. It will silently ignore
    fields that it does not know how to manage.'''
    headers=OrderedDict()
    for field in self.model._meta.fields:
      if isinstance(field, models.IntegerField) or isinstance(field, models.FloatField) or isinstance(field, models.DecimalField):
        headers[field.name] = '@attribute {} numeric'.format(field.name)
      elif isinstance(field, models.CharField) or isinstance(field, models.TextField):
        headers[field.name] = '@attribute {} string'.format(field.name)
      elif isinstance(field, models.DateTimeField):
        headers[field.name] = '@attribute {} date "yyyy-MM-dd HH:mm:ss"'.format(field.name)
      elif isinstance(field, models.DateField):
        headers[field.name] = '@attribute {} date "yyyy-MM-dd"'.format(field.name)
      elif isinstance(field, models.BooleanField):
        headers[field.name] = '@attribute {} {{True, False}}'.format(field.name)
      elif isinstance(field, models.ForeignKey):
        headers[field.name] = '@attribute {} {{{}}}'.format(field.name, ', '.join('"{}"'.format(choice[1]) for choice in field.get_choices()[1:]))
    return headers

  def toArff(self, writeable, expanded=False, relationName='relation'):
    '''outputs to an arff file-like object'''
    writeable.write('%arff file generated by the Dark Reactions Project provided by Haverford College\n')
    writeable.write('\n@relation compounds\n')
    if expanded:
      headers = self.expandedArffHeaders
      writeable.write('\n'.join(headers.values()))
    else:
      headers= self.arffHeaders
      writeable.write('\n'.join(headers.values()))
    
    writeable.write('\n\n@data\n')
    for item in self:
      if expanded:
        writeable.write(','.join(str(item.expandedValues.get(key, '?')) for key in headers.keys()))
      else:
        writeable.write(','.join(str(item.values.get(key, '?')) for key in headers.keys()))
      writeable.write('\n')
