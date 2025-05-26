from datetime import datetime
import requests 
from flask import request, jsonify
from config import Config
from user_route import auth
from models import User, UserSearchHistory
from app import app, db
from flask_httpauth import HTTPTokenAuth

from app import app

@auth.verify_token
def verify_token(token):
    return User.verify_auth_token(token)


# Route to return a list of countries and their capitals
@app.route('/country_list', methods=['GET'])
@auth.login_required
def get_country_list():
    try:
        # Fetching data from the RestCountries API
        url = "https://restcountries.com/v3.1/all"
        response = requests.get(url)
        all_countries = response.json()

        # list of dictionaries containing only country names and capitals
        country_list = []
        for country in all_countries:
            country_info = {
                'country_name': country.get('name', {}).get('common'),
                'capital': country.get('capital', [None])[0]
            }
            country_list.append(country_info)

        # Tracking the user's access to the country list (not individual countries)
        user_id = auth.current_user().id
        history_entry = UserSearchHistory(
            user_id=user_id,
            search_type='country_list', 
            viewed_at=datetime.now() 
        )
        db.session.add(history_entry)

        db.session.commit() 

        return jsonify(country_list), 200

    except Exception as e:
        db.session.rollback() 
        return jsonify({'error': str(e)}), 500







@app.route('/search_by_capital', methods=['POST'])
@auth.login_required
def search_by_capital():
    data = request.get_json()
    if not data or 'capital' not in data:
        return jsonify({'error': 'capital is required'}), 400

    capital_name_input = data['capital'].strip().lower()

    try:
        response = requests.get("https://restcountries.com/v3.1/all")
        response.raise_for_status()
        all_countries = response.json()

        # Match country by capital name (case-insensitive)
        matched_country = next(
            (c for c in all_countries
             if 'capital' in c and isinstance(c['capital'], list) and any(
                 capital.lower() == capital_name_input for capital in c['capital']
             )),
            None
        )

        if not matched_country:
            return jsonify({'error': 'Capital not found'}), 404

        # Save search history
        new_history = UserSearchHistory(
            user_id=auth.current_user().id,
            country_name=matched_country['name']['common'],
            search_type='search_by_capital'
        )
        db.session.add(new_history)
        db.session.commit()

        # Extract specific information about the matched country
        result = {
            'country_name': matched_country['name']['common'],
            'official_name': matched_country['name']['official'],
            'capital': matched_country.get('capital', [None])[0],
            'region': matched_country.get('region'),
            'subregion': matched_country.get('subregion'),
            'population': matched_country.get('population'),
            'calling_code': matched_country.get('idd', {}).get('root', '') +
                            matched_country.get('idd', {}).get('suffixes', [''])[0],
            'timezones': matched_country.get('timezones', []),
            'currencies': list(matched_country.get('currencies', {}).values()),
            'languages': list(matched_country.get('languages', {}).values()),
            'flag': matched_country.get('flags', {}).get('svg'),
            'latlng': matched_country.get('latlng', []),
            'tld': matched_country.get('tld', [])
        }

        return jsonify(result), 200

    except requests.RequestException as e:
        return jsonify({'error': 'Failed to fetch data from API', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Server error', 'details': str(e)}), 500

    



# Route to get custom information about a country
# This route allows the user to specify which fields they want to retrieve
@app.route('/country_custom_info', methods=['POST'])
@auth.login_required
def get_country_custom_info():
    data = request.get_json()

    if not data or 'country_name' not in data:
        return jsonify({'error': 'country_name is required'}), 400

    country_name_input = data['country_name'].strip().lower()
    requested_fields = data.get('fields', [])

    try:
        url = "https://restcountries.com/v3.1/all"
        response = requests.get(url)
        all_countries = response.json()

        matched_country = next(
            (c for c in all_countries 
             if c.get('name', {}).get('common', '').lower() == country_name_input 
             or c.get('name', {}).get('official', '').lower() == country_name_input),
            None
        )

        if not matched_country:
            return jsonify({'error': 'Country not found'}), 404

        result = {
            'country_name': matched_country.get('name', {}).get('common')
        }

        field_map = {
            'capital': lambda c: c.get('capital', [None])[0],
            'calling_code': lambda c: c.get('idd', {}).get('root', '') + c.get('idd', {}).get('suffixes', [''])[0],
            'population': lambda c: c.get('population'),
            'tld': lambda c: c.get('tld', [None])[0],
            'timezones': lambda c: c.get('timezones', []),
            'currencies': lambda c: list(c.get('currencies', {}).values()),
            'flag': lambda c: c.get('flags', {}).get('svg'),
            'languages': lambda c: list(c.get('languages', {}).values()),
            'latlng': lambda c: c.get('latlng', [])
        }

        if not requested_fields:
            requested_fields = list(field_map.keys())

        for field in requested_fields:
            if field in field_map:
                result[field] = field_map[field](matched_country)

        # Save search to history
        new_history = UserSearchHistory(
            user_id=auth.current_user().id,
            country_name=matched_country.get('name', {}).get('common'),
            search_type='custom_info',
            extra_info=','.join(requested_fields)
        )
        db.session.add(new_history)
        db.session.commit()

        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/search_by_country', methods=['POST'])
@auth.login_required
def search_by_country():
    data = request.get_json()
    if not data or 'country_name' not in data:
        return jsonify({'error': 'country_name is required'}), 400

    country_name_input = data['country_name'].strip().lower()

    try:
        response = requests.get("https://restcountries.com/v3.1/all")
        response.raise_for_status()
        all_countries = response.json()

        # Match by common or official name (case-insensitive)
        matched_country = next(
            (c for c in all_countries
             if c.get('name', {}).get('common', '').lower() == country_name_input or
                c.get('name', {}).get('official', '').lower() == country_name_input),
            None
        )

        if not matched_country:
            return jsonify({'error': 'Country not found'}), 404

        # Save search history
        new_history = UserSearchHistory(
            user_id=auth.current_user().id,
            country_name=matched_country['name']['common'],
            search_type='search_by_country'
        )
        db.session.add(new_history)
        db.session.commit()


         # Extract specific information
        result = {
            'country_name': matched_country['name']['common'],
            'official_name': matched_country['name']['official'],
            'capital': matched_country.get('capital', [None])[0],
            'region': matched_country.get('region'),
            'subregion': matched_country.get('subregion'),
            'population': matched_country.get('population'),
            'calling_code': matched_country.get('idd', {}).get('root', '') +
                            matched_country.get('idd', {}).get('suffixes', [''])[0],
            'timezones': matched_country.get('timezones', []),
            'currencies': list(matched_country.get('currencies', {}).values()),
            'languages': list(matched_country.get('languages', {}).values()),
            'flag': matched_country.get('flags', {}).get('svg'),
            'latlng': matched_country.get('latlng', []),
            'tld': matched_country.get('tld', [])
        }

        return jsonify(result), 200

    except requests.RequestException as e:
        return jsonify({'error': 'Failed to fetch data from API', 'details': str(e)}), 500
    except Exception as e:
        return jsonify({'error': 'Server error', 'details': str(e)}), 500


@app.route('/history', methods=['GET'])
@auth.login_required
def get_history():
    user_id = auth.current_user().id
    history = UserSearchHistory.query.filter_by(user_id=user_id).order_by(UserSearchHistory.viewed_at.desc()).all()

    result = [
        {
            'id': item.id,
            'country_name': item.country_name,
            'search_type': item.search_type,
            'viewed_at': item.viewed_at
        }
        for item in history
    ]
    return jsonify(result), 200



@app.route('/history/<int:history_id>', methods=['DELETE'])
@auth.login_required
def delete_history_item(history_id):
    user_id = auth.current_user().id
    item = UserSearchHistory.query.filter_by(id=history_id, user_id=user_id).first()

    if not item:
        return jsonify({'error': 'History item not found'}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'History item deleted'}), 200

@app.route('/history/clear', methods=['DELETE'])
@auth.login_required
def clear_history():
    user_id = auth.current_user().id
    UserSearchHistory.query.filter_by(user_id=user_id).delete()
    db.session.commit()
    return jsonify({'message': 'All history cleared'}), 200
