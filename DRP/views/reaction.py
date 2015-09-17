'''A module containing views pertinent to the manipulation of reaction objects'''

from django.views.generic import CreateView, ListView, UpdateView
from DRP.models import PerformedReaction, OrdRxnDescriptorValue, CompoundQuantity
from DRP.models import NumRxnDescriptorValue, BoolRxnDescriptorValue, CatRxnDescriptorValue
from DRP.forms import PerformedRxnForm
from DRP.forms import NumRxnDescValForm, OrdRxnDescValForm, BoolRxnDescValForm, CatRxnDescValForm  
from django.utils.decorators import method_decorator
from decorators import userHasLabGroup, hasSignedLicense, labGroupSelected
from django.contrib.auth.decorators import login_required
from django.forms.models import modelformset_factory
from DRP.forms import ModelFormSet, FormSet
from django.forms.formsets import TOTAL_FORM_COUNT
from django.shortcuts import render, redirect
from django.http import Http404

class ListPerformedReactions(ListView):
  '''Standard list view of performed reactions, adjusted to deal with a few DRP idiosyncrasies'''

  template_name='reactions_list.html'
  context_object_name='reactions'
  model=PerformedReaction 
  
  @method_decorator(login_required)
  @method_decorator(hasSignedLicense)
  @method_decorator(userHasLabGroup)
  @labGroupSelected #sets self.labGroup
  def dispatch(self, request, *args, **kwargs):
    self.queryset = PerformedReaction.objects.filter(reaction_ptr__in=self.labGroup.reaction_set.all()) | PerformedReaction.objects.filter(public=True)
    return super(ListPerformedReactions, self).dispatch(request, *args, **kwargs)

  def get_context_data(self, **kwargs):
    context = super(ListPerformedReactions, self).get_context_data(**kwargs)
    context['lab_form'] = self.labForm
#    context['filter_formset'] = self.filterFormSet
    return context

@login_required
@hasSignedLicense
@userHasLabGroup
def reactionForm(request, pk=None):
  '''A view designed to create performed reaction instances'''
  descFields = ('descriptor', 'value')
  if pk == None:
    reaction = None
  else:
    try:
      reaction=PerformedReaction.objects.get(pk=pk)
    except PerformedReaction.DoesNotExist:
      raise Http404("This reaction cannot be found")
  if reaction is not None:
    reactants = CompoundQuantity.objects.filter(reaction=reaction.reaction_ptr)
    numRxnDescriptorValues = NumRxnDescriptorValue.objects.filter(reaction=reaction.reaction_ptr)
    ordRxnDescriptorValues = OrdRxnDescriptorValue.objects.filter(reaction=reaction.reaction_ptr)
    boolRxnDescriptorValues = BoolRxnDescriptorValue.objects.filter(reaction=reaction.reaction_ptr)
    catRxnDescriptorValues = CatRxnDescriptorValue.objects.filter(reaction=reaction.reaction_ptr) 
  else:
    reactants=None
    numRxnDescriptorValues = None 
    ordRxnDescriptorValues = None
    boolRxnDescriptorValues = None
    catRxnDescriptorValues = None
    
  if request.method=='POST':
    reactantsFormSetInst = ModelFormSet(CompoundQuantity, fields=('compound', 'role', 'amount'), data=request.POST, canAdd=True, canDelete=True, instances=reactants)
    reactionForm = PerformedRxnForm(request.user, data=request.POST, instance=reaction) 

    descriptorFormSets = (
      ModelFormSet(NumRxnDescriptorValue, formClass=NumRxnDescValForm, data=request.POST, prefix='num', canDelete=True, instances=numRxnDescriptorValues),
      ModelFormSet(OrdRxnDescriptorValue, formClass=OrdRxnDescValForm, data=request.POST, prefix='ord', canDelete=True, instances=ordRxnDescriptorValues),
      ModelFormSet(BoolRxnDescriptorValue, formClass=BoolRxnDescValForm, data=request.POST, prefix='bool', canDelete=True, instances=boolRxnDescriptorValues),
      ModelFormSet(CatRxnDescriptorValue, formClass=CatRxnDescValForm, data=request.POST, prefix='cat', canDelete=True, instances=catRxnDescriptorValues)
    )

    if 'save' in request.POST: 
      if reactionForm.is_valid() and reactantsFormSetInst.is_valid() and all(d.is_valid() for d in descriptorFormSets):
        rxn = reactionForm.save()
        reactants = reactantsFormSetInst.save(commit=False)
        for reactant in reactants:
          reactant.reaction=rxn.reaction_ptr
          reactant.save()
        rxn.compoundquantities_set.exclude(reactants).delete()
        for formSet in descriptorFormSets:
          descriptorValues = formSet.save(commit=False)
          for descriptorValue in descriptorValues:
            descriptorValue.reaction=rxn.reaction_ptr
            descriptorValue.save()
          rxn.descriptorvalue_set.exclude(descriptorValues).delete()
        return redirect('reactionlist')
  else:
    reactionForm = PerformedRxnForm(request.user, instance=reaction)
    reactantsFormSetInst = ModelFormSet(CompoundQuantity, fields=('compound', 'role', 'amount'), canAdd=True, instances=reactants)
    descriptorFormSets = (
      ModelFormSet(NumRxnDescriptorValue, formClass=NumRxnDescValForm, prefix='num', instances=numRxnDescriptorValues),
      ModelFormSet(OrdRxnDescriptorValue, formClass=OrdRxnDescValForm, prefix='ord', instances=ordRxnDescriptorValues),
      ModelFormSet(BoolRxnDescriptorValue, formClass=BoolRxnDescValForm, prefix='bool', instances=boolRxnDescriptorValues),
      ModelFormSet(CatRxnDescriptorValue, formClass=CatRxnDescValForm, prefix='cat', instances=catRxnDescriptorValues)
    )
  return render(request, 'reaction_form.html', {'reaction_form':reactionForm, 'reactants_formset':reactantsFormSetInst, 'descriptor_formsets':descriptorFormSets}) 
