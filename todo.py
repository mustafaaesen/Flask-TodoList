from flask import Flask,render_template,redirect,url_for,request,flash,session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField,validators,TextAreaField,FileField
from wtforms.validators import DataRequired, Email, EqualTo, Length
import os
import uuid
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import check_password_hash
from flask import session
from dotenv import load_dotenv
import os

app=Flask(__name__)

load_dotenv()

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

db = SQLAlchemy(app)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=[]
)

@app.errorhandler(400)
@app.errorhandler(401)
@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(405)
@app.errorhandler(408)
@app.errorhandler(429)
@app.errorhandler(500)
@app.errorhandler(502)
@app.errorhandler(503)
@app.errorhandler(504)
def handle_error(e):

    code = getattr(e, 'code', 500)

    messages = {
        400: {
            "title": "Oops! Geçersiz İstek",
            "description": "Sunucu isteğinizi anlayamadı. Lütfen form veya veri girişinizi kontrol edin."
        },
        401: {
            "title": "Oops! Yetkilendirme Gerekli",
            "description": "Bu sayfaya erişmek için giriş yapmanız gerekiyor."
        },
        403: {
            "title": "Oops! Erişim Engellendi",
            "description": "Bu işlemi yapmanız için gerekli izniniz yok."
        },
        404: {
            "title": "Oops! Sayfa Bulunamadı",
            "description": "Aradığınız sayfa taşınmış, silinmiş veya hiç var olmamış olabilir."
        },
        405: {
            "title": "Oops! Geçersiz İstek Yöntemi",
            "description": "Bu URL için kullandığınız HTTP yöntemi desteklenmiyor."
        },
        408: {
            "title": "Oops! İstek Zaman Aşımına Uğradı",
            "description": "Sunucu isteğinizi zamanında alamadı. Lütfen daha sonra tekrar deneyiniz."
        },
        429: {
            "title": "Oops! Çok Fazla İstek Gönderildi",
            "description": "Kısa sürede çok fazla işlem yaptınız. Lütfen birkaç dakika bekleyip tekrar deneyin."
        },
        500: {
            "title": "Oops! Sunucu Hatası",
            "description": "Beklenmeyen bir hata oluştu."
        },
        502: {
            "title": "Oops! Geçersiz Sunucu Yanıtı",
            "description": "Sunucu geçersiz bir yanıt döndürdü."
        },
        503: {
            "title": "Oops! Sunucu Kullanılamıyor",
            "description": "Sunucu geçici olarak kullanılamıyor. Lütfen daha sonra tekrar deneyin."
        },
        504: {
            "title": "Oops! Ağ Geçidi Zaman Aşımı",
            "description": "Sunucular arasında bağlantı zaman aşımına uğradı."
        }
    }

    message = messages.get(code, {
        "title": "Oops! Bilinmeyen Hata",
        "description": "Bilinmeyen bir hata meydana geldi."
    })

    return render_template(
        "errors.html",
        code=code,
        title=message["title"],
        description=message["description"]
    ), code



def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Bu sayfaya erişmek için giriş yapmalısın.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

class RegisterForm(FlaskForm):
    
    firstname=StringField("İsim", validators=[validators.Length(min=3,max=30),validators.DataRequired()])
    lastname=StringField("Soyisim", validators=[validators.Length(min=3,max=30),validators.DataRequired()])
    username=StringField("Kullanıcı Adı", validators=[validators.Length(min=5,max=50),validators.DataRequired()])
    email=StringField("E-Posta Adresi", validators=[validators.Email(message="Lütfen Geçerli Bir E-Posta Adresi Giriniz"),validators.DataRequired()])
    password=PasswordField("Parola",validators=[
        validators.DataRequired(message="Lütfen Bir Parola Belirleyin"),
        validators.EqualTo(fieldname="confirm",message="Girilen Parolalar Aynı Değil")
    ])
    confirm=PasswordField("Parolanızı Doğrulayın")
    submit = SubmitField("Kayıt Ol")

class LoginForm(FlaskForm):
    username=StringField("Kullanıcı Adı",validators=[DataRequired()])
    password=PasswordField("Parola",validators=[DataRequired()])
    submit = SubmitField("Giriş Yap")


class TodoForm(FlaskForm):

    title=StringField("Görev Başlığı",validators=[validators.Length(min=4,max=100),validators.DataRequired(message="Görev Başlığı Boş Olamaz!!!")])
    content=TextAreaField("Görev Açıklaması",validators=[validators.DataRequired(message="Görev Açıklaması Boş Olamaz!!!")])
    image = FileField("Todo Görseli (Opsiyonel)")
    submit=SubmitField("Görev Ekle")


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(30))
    lastname = db.Column(db.String(30))
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text)

    image = db.Column(db.String(200), nullable=True)  
    # todo görseli eklenmeyedebilir

    status = db.Column(db.String(20), default="active")

    priority = db.Column(db.String(10), default="medium")


    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))



@app.route("/")
def index():
    
    todos=Todo.query.all()#veritabanından bilgileri sözlük şeklinde getirir

    return render_template("index.html",todos=todos)


#Kayıt olma

@app.route("/register",methods=["GET","POST"])
@limiter.limit("3 per minute")
def register():
    form=RegisterForm()

    if request.method=="POST":
        #formdan verilerin alınması
        firstname=form.firstname.data
        lastname=form.lastname.data 
        username=form.username.data
        email=form.email.data
        password=form.password.data

        #kullanıcı adı email kayıtlı olup olmadığı kontrolü unique lik için

        user_username=User.query.filter_by(username=username).first()
        #db den kayıt varmı kontrolü
        user_email=User.query.filter_by(email=email).first()

        if user_username:

            flash("Bu kullanıcı adı daha önce alınmış","danger")
            return render_template("register.html",form=form)
        
        if user_email:

            flash("Bu e-posta adresi ile daha önce kayıt oluşturulmuş","danger")

            return render_template("register.html",form=form)
        
        hashed_password=generate_password_hash(password)#şifreyi hashleme

        #yeni kullancıı ekleme sorgusu

        new_user=User(
            firstname=firstname,
            lastname=lastname,
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit() #ekelem ve değişiklikleri kaydetme

        flash("Kayıt işlemi başarılı! Giriş yapabilirsiniz...","success")
        return redirect(url_for("login"))



    else:

        return render_template("register.html",form=form)



# giriş yapma



@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():

    form = LoginForm()

    # WTForms ile POST + validation kontrolü
    if form.validate_on_submit():

        # formdan gelen kullanıcı adı ve parola bilgileri alınır
        username = form.username.data
        password = form.password.data

        # kullanıcı adına göre veritabanında kullanıcı aranır
        user = User.query.filter_by(username=username).first()

        # kullanıcı adı mevcutsa parola kontrolüne geçilir
        if user:

            # hashlenmiş parola ile girilen parolanın karşılaştırılması
            if check_password_hash(user.password, password):
                # parola doğruysa kullanıcı giriş yapmıştır
                # session bilgileri aktif edilir

                session["logged_in"] = True
                session["user_id"] = user.id
                session["username"] = user.username

                flash(f"Giriş Başarılı! Hoşgeldiniz {user.username}", "success")
                return redirect(url_for("index"))  # başarılı giriş sonrası yönlendirme

            else:
                # parola hatalıysa bu bloğa düşer
                flash("Parolanız hatalı!", "danger")

        else:
            # kullanıcı adı veritabanında bulunamazsa bu mesaj gösterilir
            flash("Kullanıcı adı bulunamadı!", "danger")

    # GET isteği veya validation hatası durumunda login formu tekrar gösterilir
    return render_template("login.html", form=form)



@app.route("/logout")
def logout():

    session.clear()

    flash("Çıkış başarılı!Görüşmek Üzere...","success")

    return redirect(url_for("index"))


#Todo Ekleme

@app.route("/todo/add",methods=["GET","POST"])
@login_required

def addtodo():

    form=TodoForm() #form nesnei oluşturma

    if form.validate_on_submit(): #form dolu ve istenilen şartlar sağlnmışsa istek POST tur ve görev eklenmiştir

        image_path=None#başlangıçta görsel yolu boş

        image_file=form.image.data #görselin alınması

        if image_file and image_file.filename != "": #görsel varsa

            filename=secure_filename(image_file.filename) #dosya adı alma

            unique_name=f"{uuid.uuid4().hex}_{filename}"#çaı-kışma ihtimaline karşılık qniwue isimlendirme yeniden

            save_path=os.path.join("static/todo_images",unique_name)#kaydedileceği dosya

            image_file.save(save_path) #fiziksel olarak kaydetme

            image_path=f"todo_images/{unique_name}" #db ye kaydedilecek dosya yolu 


        new_todo=Todo( #ekleme komutu yazımı
            title=form.title.data,
            content=form.content.data,
            image=image_path,
            user_id=session.get("user_id"),
            status="active"

        )

        db.session.add(new_todo) # db ekleme
        db.session.commit() #değişikliklerin tamamlanması

        flash("Görev Ekleme Başarılı!!!","success")
        return redirect(url_for("index"))
    
    

    return render_template("addtodo.html",form=form)


@app.route("/dashboard")
@login_required
def dashboard():

    if "user_id" not in session:
        flash("Bu sayfayı görüntüleyebilmek için lütfen giriş yapınız","danger")
        return redirect(url_for("login"))
    
    user_id=session.get("user_id")

    todos=Todo.query.filter_by(user_id=user_id).all()
    #kullanıcının tüm todolarını çekme

    return render_template("dashboard.html",todos=todos)

#todo görüntüleme
#kullanıcı card ile görüntüleyebilmesi için
#işler backend de ayrıldı ama frontendde ayrı endpoint uygulanamdı
#ilgili kısmda aynı endpoint içinde sdece ilgili yer değişiyor
#tek template(dashboard) ile yapbilmek için dashboard html in beklediği şeyleri gönderek gerekli
@app.route("/dashboard/todo/<int:id>")
@login_required
def dashboard_todo_detail(id):


    if "user_id" not in session:
        flash("Bu sayfayı görütüleyebilmek için lütfen giriş yapınız!!!","danger")
        return redirect(url_for("login"))
    

    selected_todo=Todo.query.get_or_404(id)

    if selected_todo.user_id != session.get("user_id"):

        flash("Bu Todo'ya erişim yetkiniz yok!!!","danger")
        return redirect(url_for("dashboard"))
    
    todos=Todo.query.filter_by(user_id=session.get("user_id")).all()
    #kullanıcının todoalrını ve seçilen todoyu alıp gönderme 

    mode = request.args.get("mode", "view")

    return render_template("dashboard.html",todos=todos,selected_todo=selected_todo,mode=mode)
    #sadce görüntüleme için ayrı mode templete a render edildi
#güncelleme

@app.route("/dashboard/todo/<int:id>/update", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def dashboard_todo_update(id):

    # dashboard todo detail'den halihazırda olan bilgileri alarak gösterir
    # kullanıcı edit'e basınca bilgiler gelir, düzenlenebilir
    # güncelleme tamamlanınca POST ile yeni bilgiler alınır ve DB'ye yazılır

    if "user_id" not in session:
        flash("Bu sayfayı görüntüleyebilmek için lütfen giriş yapınız!!!", "danger")
        return redirect(url_for("login"))

    todo = Todo.query.get_or_404(id)
    # todo'yu alma

    if todo.user_id != session.get("user_id"):
        # başkasının todo'sunu güncellemeyi önleme
        flash("Bu işlemi yapmaya yetkiniz yok!!!", "danger")
        return redirect(url_for("dashboard"))



    old_title = todo.title
    old_content = todo.content
    old_image = todo.image

    updated = False  # gerçekten güncelleme oldu mu?


    new_title = request.form.get("title")
    new_content = request.form.get("content")

    if new_title != old_title:
        todo.title = new_title
        updated = True

    if new_content != old_content:
        todo.content = new_content
        updated = True



    image_file = request.files.get("image")

    if image_file and image_file.filename != "":
        filename = secure_filename(image_file.filename)
        unique_name = f"{uuid.uuid4().hex}_{filename}"
        save_path = os.path.join("static/todo_images", unique_name)
        image_file.save(save_path)

        todo.image = f"todo_images/{unique_name}"
        updated = True  # görsel değiştiyse de update var



    if updated:
        db.session.commit()
        flash("Todo Güncelleme Başarılı!!!", "success")
    else:
        flash("Herhangi bir değişiklik yapılmadı.", "info")

    return redirect(url_for("dashboard_todo_detail", id=id))


    
@app.route("/dashboard/todo/<int:id>/toggle",methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def toggle_todo_status(id):
    #todo nun durumunu güncelleme için kullanılır aktif ise tamamlandı
    #tmamlandı ise aktif şeklinde geri dönmek için

    if "user_id" not in session:
        flash("Bu sayfayı görüntüleyebilmek için giriş yapmalısınız!!!","danger")
        return redirect(url_for("login"))
    
    todo=Todo.query.get_or_404(id) # durumu değişecek todo nun alınması

    if todo.user_id != session.get("user_id"):
        flash("Bu işlemi yapmaya yetkiniz yok!!!","danger")
        return redirect(url_for("dashboard"))
    

    #toggle durumu güncelleme

    if todo.status == "active":
        todo.status="done"

        flash("Todo Tamamlandı!","success")
    
    else:
        todo.status="active"
        flash("Todo tekrar aktif edildi!","info")
    
    db.session.commit()

    return redirect(url_for("dashboard"))


#önceliklendirme dereceleri

@app.route("/dashboard/todo/<int:id>/priority",methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def update_todo_priority(id):


    if "user_id" not in session:
        flash("Bu sayfayı görüntüleyebilmek için giriş yapmalısınız!","danger")
        return redirect(url_for("login"))
    
    todo=Todo.query.get_or_404(id)

    if todo.user_id != session.get("user_id"):

        flash("Bu işlemi yapmaya yetkiniz yok","danger")
        return redirect(url_for("dashboard"))
    

    priority=request.form.get("priority")
    #mvcut özelliği alma

    if priority not in ("high","medium","low"):

        flash("Geçersiz öncelik değeri","danger")

        return redirect(url_for("dashboard"))
    
    #ekstra güvenlik önlemi

    todo.priority=priority
    db.session.commit()

    messages={

        "high":"Todo yüksek öncelik olarak işaretlendi",
        "medium":"Todo orta öncelik olarak işaretlendi",
        "low":"Todo düşük öncelik olarak işaretlendi"
    }

    flash(messages[priority], "success")

    return redirect(url_for("dashboard"))


@app.route("/dashboard/todo/<int:id>/delete",methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def delete_todo(id):


    if "user_id" not in session:

        flash("Bu işlemi yapmak için giriş yapmalısınız!!!","danger")
        return redirect(url_for("login"))
    
    todo=Todo.query.get_or_404(id)

    if todo.user_id != session.get("user_id"):

        flash("Bu işlemi yapmak için yetkiniz yok!!!","danger")
        return redirect(url_for("dashboard"))
    
    db.session.delete(todo)
    db.session.commit()

    flash("Todo silme başarılı!!!","success")

    return redirect(url_for("dashboard"))

    
@app.route("/todos/active")
@login_required

def active_todos():

    if "user_id" not in session:

        flash("Bu sayfayı görütüleyebilmek için giriş yapmalısınız!!!","danger")

        return redirect(url_for("login"))
    
    todos=Todo.query.filter_by(user_id=session["user_id"],status="active").all()


    return render_template("active.html",todos=todos)

    
@app.route("/todos/done")
@login_required
def done_todos():

    if "user_id" not in session:

        flash("Bu sayfayı görüntüleyebilmek için giriş yapmalısınız!!!","danger")
        return redirect(url_for("login"))
    
    todos=Todo.query.filter_by(user_id=session["user_id"],status="done").all()

    return render_template("done.html",todos=todos)


