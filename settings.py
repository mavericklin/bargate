#!/usr/bin/python
#
# This file is part of Bargate.
#
# Bargate is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Bargate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Bargate.  If not, see <http://www.gnu.org/licenses/>.

from bargate import app
import bargate.core
from flask import Flask, request, session, redirect, url_for, render_template, flash, g, abort
import kerberos
import mimetypes
import os 
from random import randint
import time
import json

################################################################################

def get_user_theme():
	if 'username' in session:
		try:
			theme = g.redis.get('user:' + session['username'] + ':theme')

			if theme != None:
				return theme
				
		except Exception as ex:
			## Can't return an error, this function is called from jinja.
			app.logger.error('Unable to speak to redis: ' + str(ex))

	## If we didn't return a new theme, return the default from the config file
	return app.config['THEME_DEFAULT']

################################################################################

def get_user_navbar():
	if 'username' in session:
		try:
			navbar = g.redis.get('user:' + session['username'] + ':navbar_alt')

			if navbar != None:
				return navbar
			else:
				return 'default'
					
		except Exception as ex:
			## Can't return an error, this function is called from jinja.
			app.logger.error('Unable to speak to redis: ' + str(ex))

	return 'default'

################################################################################

def show_hidden_files():
	if 'username' in session:
		try:
			hidden_files = g.redis.get('user:' + session['username'] + ':hidden_files')

			if hidden_files != None:
				if hidden_files == 'show':
					return True

		except Exception as ex:
			app.logger.error('Unable to speak to redis: ' + str(ex))

	return False
	
################################################################################

def upload_overwrite():
	if 'username' in session:
		try:
			upload_overwrite = g.redis.get('user:' + session['username'] + ':upload_overwrite')

			if upload_overwrite != None:
				if upload_overwrite == 'yes':
					return True

		except Exception as ex:
			app.logger.error('Unable to speak to redis: ' + str(ex))

	return False
	
################################################################################

def get_on_file_click():
	if 'username' in session:
		try:
			on_file_click = g.redis.get('user:' + session['username'] + ':on_file_click')

			if on_file_click != None:
				return on_file_click
			else:
				return 'ask'

		except Exception as ex:
			app.logger.error('Unable to speak to redis: ' + str(ex))

	return 'ask'
	
################################################################################

def set_user_data(key,value):
	g.redis.set('user:' + session['username'] + ':' + key,value)

################################################################################
#### Account Settings View

@app.route('/settings', methods=['GET','POST'])
@bargate.core.login_required
@bargate.core.downtime_check
def settings():

	themes = []
	themes.append({'name':'Lumen','value':'lumen'})
	themes.append({'name':'Journal','value':'journal'})
	themes.append({'name':'Flatly','value':'flatly'})
	themes.append({'name':'Readable','value':'readable'})
	themes.append({'name':'Simplex','value':'simplex'})
	themes.append({'name':'Spacelab','value':'spacelab'})
	themes.append({'name':'United','value':'united'})
	themes.append({'name':'Cerulean','value':'cerulean'})
	themes.append({'name':'Darkly - may not function correctly','value':'darkly'})
	themes.append({'name':'Cyborg - may not function correctly','value':'cyborg'})
	themes.append({'name':'Slate - may not function correctly','value':'slate'})

	
	if request.method == 'POST':
	
		## Set theme
		new_theme = request.form['theme']
		
		## check theme is valid
		theme_set = False
		for theme in themes:
			if new_theme == theme['value']:
				bargate.settings.set_user_data('theme',new_theme)
				theme_set = True
				
		if not theme_set:
			flash('Invalid theme choice','alert-danger')
			return bargate.core.render_page('settings.html', active='user', themes=themes)
			
		## navbar inverse/alt
		if 'navbar_alt' in request.form:
			navbar_alt = request.form['navbar_alt']
			if navbar_alt == 'inverse':
				bargate.settings.set_user_data('navbar_alt','inverse')
			else:
				bargate.settings.set_user_data('navbar_alt','default')
		else:
			bargate.settings.set_user_data('navbar_alt','default')
					
		## Set hidden files
		if 'hidden_files' in request.form:
			hidden_files = request.form['hidden_files']
			if hidden_files == 'show':
				bargate.settings.set_user_data('hidden_files','show')
			else:
				bargate.settings.set_user_data('hidden_files','hide')
		else:
			bargate.settings.set_user_data('hidden_files','hide')
			
		## Upload overwrite
		if 'upload_overwrite' in request.form:
			upload_overwrite = request.form['upload_overwrite']
			
			if upload_overwrite == 'yes':
				bargate.settings.set_user_data('upload_overwrite','yes')
			else:
				bargate.settings.set_user_data('upload_overwrite','no')
		else:
			bargate.settings.set_user_data('upload_overwrite','no')
			
		## On file click
		if 'on_file_click' in request.form:
			on_file_click = request.form['on_file_click']
			
			if on_file_click == 'download':
				bargate.settings.set_user_data('on_file_click','download')
			elif on_file_click == 'default':
				bargate.settings.set_user_data('on_file_click','default')
			else:
				bargate.settings.set_user_data('on_file_click','ask')
		else:
			bargate.settings.set_user_data('on_file_click','ask')
						
		flash('Settings saved','alert-success')
		return redirect(url_for('settings'))
				
	elif request.method == 'GET':
	
		if bargate.settings.show_hidden_files():
			hidden_files = 'show'
		else:
			hidden_files = 'hide'
			
		if bargate.settings.upload_overwrite():
			upload_overwrite = 'yes'
		else:
			upload_overwrite = 'no'
	
		return bargate.core.render_page('settings.html', 
			active='user',
			themes=themes, 
			hidden_files=hidden_files,
			upload_overwrite=upload_overwrite,
			on_file_click = bargate.settings.get_on_file_click(),
		)
