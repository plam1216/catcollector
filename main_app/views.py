from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.http import HttpResponse
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

import uuid
import boto3

from .models import Cat, Toy, Photo
from .forms import FeedingForm

# Add these "constants" below the imports
S3_BASE_URL = 'https://s3.us-east-1.amazonaws.com/'
BUCKET = 'cat-collector-titans-8'

# Create your views here.
def signup(request):
  error_message = ''
  if request.method == 'POST':
    # This is how to create a 'user' form object
    # that includes the data from the browser
    form = UserCreationForm(request.POST)
    if form.is_valid():
      # This will add the user to the database
      user = form.save()
      # This is how we log a user in via code
      login(request, user)
      return redirect('index')
    else:
      error_message = 'Invalid sign up - try again'
  # A bad POST or a GET request, so render signup.html with an empty form
  form = UserCreationForm()
  context = {'form': form, 'error_message': error_message}
  return render(request, 'registration/signup.html', context)

def home(request):
    ''' return a response in most cases render a template we will need some dat for the template in most cases '''
    # return HttpResponse('<h1>Hello World</h1>')
    return render(request, 'home.html')

def about(request):
    # return HttpResponse('<h1>About the CatCollector</h1>')
    return render(request, 'about.html')

@login_required
def cats_index(request):
  # This reads ALL cats, not just the logged in user's cats
  # cats = Cat.objects.all()
  # return render(request, 'cats/index.html', {'cats':cats})

  cats = Cat.objects.filter(user=request.user)
  # You could also retrieve the logged in user's cats like this
  # cats = request.user.cat_set.all()
  return render(request, 'cats/index.html', { 'cats': cats })

@login_required
def cats_detail(request, cat_id):
  cat = Cat.objects.get(id=cat_id)

  # instantiate FeedingForm to be rendered in the template
  feeding_form = FeedingForm()

  # displaying unassociated toys
  toys_cat_doesnt_have = Toy.objects.exclude(id__in = cat.toys.all().values_list('id'))

  return render(request, 'cats/detail.html', {
    'cat': cat,
    'feeding_form': feeding_form,
    'toys': toys_cat_doesnt_have,
  })

@login_required
def add_feeding(request, cat_id):
  # create the ModelForm using the data in request.POST
  form = FeedingForm(request.POST)
  # validate the form
  if form.is_valid():
    # don't save the form to the db until it
    # has the cat_id assigned
    new_feeding = form.save(commit=False)
    new_feeding.cat_id = cat_id
    new_feeding.save()
  return redirect('detail', cat_id=cat_id)

@login_required
def assoc_toy(request, cat_id, toy_id):
  # you can pass a toy's id instead of the whole object
  Cat.objects.get(id=cat_id).toys.add(toy_id)
  return redirect('detail', cat_id=cat_id)

@login_required
def add_photo(request, cat_id):
  # attempt to collect the photo file data
    # FILES is a dictionary
    # photo-file will be the "name" attribute on the <input type="file">
      # creates key 'photo-file'; if file is not present key is 'None'
  photo_file = request.FILES.get('photo-file', None)

  # use conditional logic to determine if the file is present
  if photo_file:

  # if it is present, we will create a reference to the boto3 client
    s3 = boto3.client('s3')

    # create a unique id for each photo file S3 / needs image file extension too
                              # access photo_file name; 
                              # access the 'name' string; 
                              # 'rfind' is python string method, look for specific char in string; returns index
                              # ':' slice off extension => abcd.jpg => abcd
                              # photo_file.name[4:]
    key = uuid.uuid4().hex[:6] + photo_file.name[photo_file.name.rfind('.'):]

    # upload the photo file to aws s3
    # just in case something goes wrong
    try:
    # if successful
      # takes 3 arguments, reference to photo object, name of BUCKET (global var), name to save file as
      s3.upload_fileobj(photo_file, BUCKET, key)
      
      # take the exchanged url and save it to the database
      # build the full url string
      url = f"{S3_BASE_URL}{BUCKET}/{key}"
      
      # 1) create photo instance with photo model and provide cat_id as foreign key value
      # we can assign to cat_id or cat (if you have a cat object)
      photo = Photo(url=url, cat_id=cat_id)
      
      # 2) save the photo instance to the database
      photo.save()
    # else print an error message
    except Exception as error:
        print('An error occurred uploading file to S3')
  # else:
    # else redirect the user to the origin page
    # return redirect('detail', cat_id=cat_id)
  return redirect('detail', cat_id=cat_id)


class CatCreate(LoginRequiredMixin, CreateView):
  model = Cat
  # fields = '__all__'
  fields = ['name', 'breed', 'description', 'age']
  # success_url = '/cats/'

  # this inherited method is called when a valid cat form is being submitted
  def form_valid(self, form):
    # assign the logged in user (self.request.user)
    form.instance.user = self.request.user # form.instance
    # Let CreateView do its just as usual
    return super().form_valid(form)

class CatUpdate(LoginRequiredMixin, UpdateView):
  model = Cat
  fields = ['breed', 'description', 'age']

class CatDelete(LoginRequiredMixin, DeleteView):
  model = Cat
  success_url = '/cats/'

class ToyCreate(LoginRequiredMixin, CreateView):
    model = Toy
    fields = ('name', 'color')

class ToyUpdate(LoginRequiredMixin, UpdateView):
    model = Toy
    fields = ('name', 'color')

class ToyDelete(LoginRequiredMixin, DeleteView):
    model = Toy
    success_url = '/toys/'

class ToyDetail(LoginRequiredMixin, DetailView):
    model = Toy
    template_name = 'toys/detail.html'

class ToyList(LoginRequiredMixin, ListView):
    model = Toy
    template_name = 'toys/index.html'