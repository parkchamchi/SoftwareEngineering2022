from django.views import View
from django.views.generic import ListView, DetailView, FormView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import UpdateView, DeleteView, CreateView  # new
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect

from guest_user.mixins import AllowGuestUserMixin

from .models import List, Task, FrontendOptions
from .forms import TaskForm

# Create your views here.

class UserCanAccessMixin:
	def get_queryset(self):
		queryset = super().get_queryset()
		queryset = queryset.filter(author=self.request.user)
		return queryset

class ListListView(AllowGuestUserMixin, LoginRequiredMixin, UserCanAccessMixin, ListView):
	model = List
	template_name = "list_list.html"
	
class TaskGet(DetailView):
	model = List
	template_name = "list_detail.html"

	def get_context_data(self, **kwargs):
		#Set form for the task
		context = super().get_context_data(**kwargs)
		context["form"] = TaskForm()
		return context
	
class TaskPost(SingleObjectMixin, FormView):
	model = List
	form_class = TaskForm
	template_name = "list_detail.html"

	def post(self, request, *args, **kwargs):
		self.object = self.get_object()
		return super().post(request, *args, **kwargs)
	
	def form_valid(self, form):
		task = form.save(commit=False)
		task.list = self.object
		task.save()
		return super().form_valid(form)
	
	def get_success_url(self):
		list = self.get_object()
		return reverse("list_detail", kwargs={"pk": list.pk})

class ListDetailView(AllowGuestUserMixin, LoginRequiredMixin, UserCanAccessMixin, View):
	def get(self, request, *args, **kwargs):
		view = TaskGet.as_view()
		return view(request, *args, **kwargs)
	
	def post(self, request, *args, **kwargs):
		view = TaskPost.as_view()
		return view(request, *args, **kwargs)

class ListUpdateView(AllowGuestUserMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = List
	fields = (
		"title",
	)
	template_name = "list_edit.html"

	def test_func(self):
		obj = self.get_object()
		return obj.author == self.request.user

class ListDeleteView(AllowGuestUserMixin, LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = List
	template_name = "list_delete.html"
	success_url = reverse_lazy("list_list")

	def test_func(self):
		obj = self.get_object()
		return obj.author == self.request.user

class ListCreateView(AllowGuestUserMixin, LoginRequiredMixin, CreateView):
	model = List
	template_name = "list_new.html"
	fields = (
		"title",
	)

	def form_valid(self, form):
		#Checks whether the author is valid
		form.instance.author = self.request.user
		return super().form_valid(form)
	
class ListSortView(AllowGuestUserMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = List
	fields = (
		"sort_criterion",
	)
	template_name = "list_sort.html"

	def test_func(self):
		obj = self.get_object()
		return obj.author == self.request.user
	
class TaskUpdateView(AllowGuestUserMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = Task
	form_class = TaskForm
	template_name = "task_edit.html"

	def test_func(self):
		obj = self.get_object()
		return obj.list.author == self.request.user

	def get_success_url(self):
		return reverse("list_list")

class TaskDeleteView(AllowGuestUserMixin, LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = Task
	template_name = "task_delete.html"
	#success_url = reverse_lazy("list_list")

	def test_func(self):
		obj = self.get_object()
		return obj.list.author == self.request.user
	
	def get_success_url(self):
		return reverse("list_list")
	
class TaskToggleDoneView(AllowGuestUserMixin, LoginRequiredMixin, UserPassesTestMixin, View):
	def post(self, request, task_id):
		task = get_object_or_404(Task, id=task_id)
		task.toggle_done()
		return redirect(request.META.get('HTTP_REFERER')) #return to the referer
	
	def test_func(self):
		task = get_object_or_404(Task, id=self.kwargs['task_id'])
		return task.list.author == self.request.user
	
class ToggleHideFinishedTasksView(AllowGuestUserMixin, LoginRequiredMixin, UserPassesTestMixin, View):
	def post(self, request):
		frontend_options = FrontendOptions.get(user=request.user)
		frontend_options.hide_finished_tasks = not frontend_options.hide_finished_tasks
		frontend_options.save()
		return redirect(request.META.get('HTTP_REFERER')) #return to the referer
	
	def test_func(self):
		return self.request.user.is_authenticated