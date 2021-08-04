from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage, get_storage_class
from django.http import HttpResponse
from django.views.generic import View
from .forms import *
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import plotly.express as px
import json
from plotly.offline import plot
import numpy as np
import k_mxt_w3


# Create your views here.

def build_2d(df, bound_form):
    try:
        if len(bound_form.cleaned_data['features']) == 0:
            fig_2d = px.scatter_mapbox(df,
                                       lat=bound_form.cleaned_data['latitude'],
                                       lon=bound_form.cleaned_data['longitude'],
                                       zoom=5,
                                       height=1000,
                                       )
        else:
            fig_2d = px.scatter_mapbox(df,
                                       lat=bound_form.cleaned_data['latitude'],
                                       lon=bound_form.cleaned_data['longitude'],
                                       hover_name=bound_form.cleaned_data['features'][0],
                                       hover_data=bound_form.cleaned_data['features'],
                                       color=bound_form.cleaned_data['features'][0],
                                       zoom=5,
                                       height=1000,
                                       color_continuous_scale=px.colors.cyclical.IceFire,
                                       )
        fig_2d.update_layout(mapbox_style="open-street-map")
        fig_2d.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        plt_2d = plot(fig_2d, output_type='div', show_link=False, link_text='', )
        return plt_2d
    except Exception as e:
        pass


class Clustering:
    def __init__(self, bound_form, df):
        self.bound_form = bound_form
        self.df = df
        self.alg = None

    def calculate_modularity(self):
        return self.alg.clusters_data.calculate_modularity(self.alg.start_graph)

    def save_clustering_result_in_file(self):
        if self.alg is None:
            raise AttributeError('clustering result is not calculated')
        clustering_result_str = json.dumps(self.alg.clusters_data.cluster_numbers.tolist())
        path = default_storage.save('clustering_result.json', ContentFile(clustering_result_str))
        return path

    def calculate_clustering_result(self):
        x, y, features = k_mxt_w3.data.DataPropertyImportSpace.get_data(
            df=self.df,
            name_latitude_cols=self.bound_form.cleaned_data['latitude'],
            name_longitude_cols=self.bound_form.cleaned_data['longitude'],
            features_list=self.bound_form.cleaned_data['features'],
        )
        clusters = k_mxt_w3.clusters_data.ClustersDataSpaceFeatures(
            x_init=x,
            y_init=y,
            features_init=features,
            metrics=self.bound_form.cleaned_data['metric'],
        )
        algorithm = None
        if self.bound_form.cleaned_data['algorithm'] == 'k_mxt_w3':
            algorithm = k_mxt_w3.clustering_algorithms.K_MXT_gauss
        elif self.bound_form.cleaned_data['algorithm'] == 'k_mxt':
            algorithm = k_mxt_w3.clustering_algorithms.K_MXT
        self.alg = algorithm(
            k=self.bound_form.cleaned_data['k'],
            eps=self.bound_form.cleaned_data['eps'],
            clusters_data=clusters,
        )
        self.alg()
        return self.alg.clusters_data.cluster_numbers

    def build_clusters(self):
        fig = px.scatter_mapbox(
            self.df,
            lat=self.bound_form.cleaned_data['latitude'],
            lon=self.bound_form.cleaned_data['longitude'],
            hover_name=self.alg.clusters_data.cluster_numbers,
            hover_data=self.bound_form.cleaned_data['features'],
            color=self.alg.clusters_data.cluster_numbers,
            zoom=5,
            height=1000,
            color_continuous_scale=px.colors.cyclical.HSV,
        )
        fig.update_layout(mapbox_style="open-street-map")
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        plt_clusters = plot(fig, output_type='div', show_link=False, link_text='', )
        return plt_clusters


class AlgorithmView(LoginRequiredMixin, View):
    template = 'clustering/clustering.html'
    form_model = FileForm
    raise_exception = False
    login_url = '/accounts/login/'

    @csrf_exempt
    def get(self, request):
        form = self.form_model(request.GET, initial={'k': '5', 'eps': 0.05})
        return render(request, self.template, context={'form': form, 'is_visible': False, 'not_show': True})

    @csrf_exempt
    def post(self, request):
        if '_upload' in request.POST:
            self.form_model = FileForm
            bound_form = self.form_model(request.POST, request.FILES)
            if bound_form.is_valid():
                source_file = request.FILES["file"]
                df = pd.read_csv(source_file)
                columns = df.select_dtypes(include=['float', 'int']).columns
                choices = [(x, x) for x in columns]
                request.session['df'] = df.to_json()
                calculate_form = AlgorithmForm(choices, request.POST)
                self.form_model = AlgorithmForm
                return render(request, self.template, context={'form': calculate_form, 'is_visible': True, 'not_show': True})
        elif '_calculate' in request.POST:
            df_json = request.session.get('df', ())
            df = pd.read_json(df_json)
            columns = df.select_dtypes(include=['float', 'int']).columns
            choices = [(x, x) for x in columns]
            bound_form = AlgorithmForm(choices, request.POST)
            if bound_form.is_valid():
                clustering = Clustering(df=df, bound_form=bound_form)
                plt_2d = build_2d(df, bound_form)
                clustering_result = clustering.calculate_clustering_result()
                path = clustering.save_clustering_result_in_file()
                plt_clusters = clustering.build_clusters()
                modularity = clustering.calculate_modularity()
                return render(request, self.template,
                              context={'form': bound_form,
                                       'is_visible': True,
                                       'plt_2d': plt_2d,
                                       'plt_clusters': plt_clusters,
                                       'modularity': modularity,
                                       # 'clustering_result': clustering_result,
                                       'filepath': path
                                       })
            else:
                return render(request, self.template, context={'form': bound_form, 'is_visible': True})
        return render(request, self.template, context={'form': bound_form, 'is_visible': False})


def download_file(request, filepath):
    file = open(filepath)
    response = HttpResponse(file, content_type='json')
    response['Content-Disposition'] = f"attachment; filename={filepath}"
    return response
