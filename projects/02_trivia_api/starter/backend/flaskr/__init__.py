import os
from flask import Flask, after_this_request, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


'''
@TODO: DONE: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
@TODO: DONE: Use the after_request decorator to set Access-Control-Allow
'''

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r'/api/*': {'origins': '*'}}) #the lecture and class notes were wrong. There should be no * in front of /api... {r"/api/*": {"origins": "*"}})
    
    #CORS headers
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')

        return response

    '''@TODO: DONE: Create an endpoint to handle GET requests for all available categories.'''

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.order_by(Category.id).all()
        
        current_categories = {}
        for category in categories:
            current_categories[category.id] = category.type

        if len(current_categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': current_categories,
            'total_categories': len(Category.query.all())
        })


    '''
    @TODO: 
    Create an endpoint to handle GET requests for questions, 
    including pagination (every 10 questions). 
    This endpoint should return a list of questions, 
    number of total questions, current category, categories. 

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions. 
    '''

    def get_category_list():
        categories = {}
        category_list = Category.query.all()

        for category in category_list:
            categories[category.id] = category.type
        
        return categories

    '''
    Please see link for help with issue I was having: https://knowledge.udacity.com/questions/116054 and 
    https://knowledge.udacity.com/questions/157335. The client was not loading the questions. I needed to
    add "categories" and "current_category" to json response. I also needed to update the URL expected in 
    the frontend from http://127.0.0.1:3000/questions?page=${this.state.page} to /questions?page=${this.state.page}
    I am not sure it should have been the frontend URL (3000 port) anyway. It should probably be 5000 port.
    '''
    @app.route('/questions/', methods=['GET']) #For some reason if I remove the / after questions, the app breaks. But curl requests omitting the second / work. 
    def get_paginated_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)

        if current_questions is None: #I used to have 'if len(current_questions == 0:' this was producing 'JSONDecodeError: Expecting value: line 1 column 1 (char 0)'. Using 'is None' fixes that for cases where HTTP returns 404. 
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection),
            'categories': get_category_list(),
            'current_category': None
        })

    '''
    @TODO: 
    Create an endpoint to DELETE question using a question ID. 

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page. 
    '''

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(selection)
            })
        except:
            abort(422)

    '''
    @TODO: 
    Create an endpoint to POST a new question, 
    which will require the question and answer text, 
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab, 
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.  

    @TODO: 
    Create a POST endpoint to get questions based on a search term. 
    It should return any questions for whom the search term 
    is a substring of the question. 

    TEST: Search by any phrase. The questions list will update to include 
    only question that include that string within their question. 
    Try using the word "title" to start. 
    '''

    @app.route('/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_category = body.get('category', None)
        new_difficulty = body.get('difficulty', None)
        search = body.get('search', None)

        try:

            if search:
                selection = Question.query.order_by(Question.id).filter(
                    Question.question.ilike('%{}%'.format(search))
                    )
                current_questions = paginate_questions(request, selection)

                return jsonify({
                    'success': True,
                    'questions': current_questions,
                    'total_questions': len(selection.all())
                })

            else:
                question = Question(
                    question=new_question, 
                    answer=new_answer, 
                    category=new_category, 
                    difficulty=new_difficulty
                    )

                question.insert()

                selection = Question.query.order_by(Question.id).all()
                categories = Category.query.order_by(Category.id).all()
                current_questions = paginate_questions(request, selection)
                categories_dict = {}

                for category in categories:
                    categories_dict[category.id] = category.type

                return jsonify({
                    'success': True,
                    'created': question.id,
                    'questions': current_questions,
                    'category': categories_dict,
                    'total_questions': len(current_questions)
                })

        except:
            abort(422)

    '''
    @TODO: 
    Create a GET endpoint to get questions based on category. 

    TEST: In the "List" tab / main screen, clicking on one of the 
    categories in the left column will cause only questions of that 
    category to be shown. 
    '''

    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def filter_by_category(category_id):
        selection = Question.query.order_by(Question.id).filter(Question.category == category_id).all()
        current_questions = paginate_questions(request, selection)

        if current_questions is None:  #I used to have 'if len(current_questions == 0:' this was producing 'JSONDecodeError: Expecting value: line 1 column 1 (char 0)'. Using 'is None' fixes that for cases where HTTP returns 404. 
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(selection)
        })


    '''
    @TODO: 
    Create a POST endpoint to get questions to play the quiz. 
    This endpoint should take category and previous question parameters 
    and return a random questions within the given category, 
    if provided, and that is not one of the previous questions. 

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not. 
    '''

    @app.route('/quizzes', methods=['POST'])
    def play_game():
        
        body = request.get_json()

        previous_questions = body.get('previous_questions', [])
        category = body.get('category', None)

        try:
            if category == 0 or category is None:
                quiz_questions = Question.query.all()
            else:
                quiz_questions = Question.query.filter(Question.category == category).all()
            
            selected_questions = []

            for question in quiz_questions:
                if question.id not in previous_questions:
                    selected_questions.append(question.format())

            if len(selected_questions) != 0:
                quest = random.choice(selected_questions)
                return jsonify({
                    'question': quest
                })
            else:
                abort(422)
        except:
            abort(404)

    '''
    @TODO: 
    Create error handlers for all expected errors 
    including 404 and 422. 
    '''

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False, 
            "error": 404, 
            "message": "resource not found"
            }),404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False, 
            "error": 422, 
            "message": "unprocessable"
            }),422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False, 
            "error": 400, 
            "message": "bad request"
            }),400

    return app