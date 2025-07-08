import time
from PIL import Image
from sqlalchemy import create_engine
from nptdms import TdmsFile
from plotly.subplots import make_subplots
from numpy.lib.stride_tricks import sliding_window_view
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import pymysql
import dotenv
import os
import concurrent.futures
import re