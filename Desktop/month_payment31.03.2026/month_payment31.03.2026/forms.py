from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SelectField, IntegerField, FloatField, RadioField, SubmitField, FileField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional, Regexp

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=1, max=128)])
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    business_name = StringField('Business Name', validators=[DataRequired(), Length(min=2, max=200)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    password = PasswordField('Password', validators=[
        DataRequired(), 
        Length(min=8, max=128, message='Password must be at least 8 characters long'),
        Regexp(
            r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]',
            message='Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character'
        )
    ])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ProductForm(FlaskForm):
    title = StringField('Product Title', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    status = SelectField('Status', choices=[('Available', 'Available'), ('Reserved', 'Reserved'), ('Sold', 'Sold')], validators=[DataRequired()])
    photo = FileField('Product Photo', validators=[Optional()])
    submit = SubmitField('List Product')

class ReviewForm(FlaskForm):
    rating = RadioField('Rating', choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')], validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Submit Review')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[Optional()])
    category = SelectField('Category', coerce=int, default=0)

class ProfileForm(FlaskForm):
    business_name = StringField('Business Name', validators=[DataRequired(), Length(min=2, max=200)])
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(max=20)])
    telegram_id = StringField('Telegram Username', validators=[Optional(), Length(max=50)])
    profile_photo = FileField( 'Profile Photo', validators=[Optional()])
    current_password = PasswordField('Current Password', validators=[Optional()])
    new_password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[Optional(), EqualTo('new_password')])
    submit = SubmitField('Update Profile')

class ForumForm(FlaskForm):
    content = TextAreaField("Message", validators=[DataRequired()])
    photo = FileField("Attach Photo", validators=[Optional()])
    submit = SubmitField("Post")

class EditPostForm(FlaskForm):
    content = TextAreaField("Edit Post", validators=[DataRequired()])
    photo = FileField("Replace Photo", validators=[Optional()])
    remove_photo = BooleanField("Remove existing photo")
    submit = SubmitField("Save Changes")

class EditReplyForm(FlaskForm):
    content = TextAreaField("Edit Reply", validators=[DataRequired()])
    photo = FileField("Replace Photo", validators=[Optional()])
    remove_photo = BooleanField("Remove existing photo")
    submit = SubmitField("Save Changes")


class ReplyForm(FlaskForm):
    content = TextAreaField("Reply", validators=[DataRequired()])
    photo = FileField("Attach Photo", validators=[Optional()])
    submit = SubmitField("Reply")