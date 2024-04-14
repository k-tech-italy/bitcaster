var $ = django.jQuery;
var $context = $("#id_context");
var $subject = $("#id_subject");
var $content = $("#id_content");
var csrftoken = $("[name=csrfmiddlewaretoken]").val();
var render_url = $("meta[name='render-url']").attr("content");  ;
var edit_url = $("meta[name='edit-url']").attr("content");  ;
var change_url = $("meta[name='change-url']").attr("content");  ;
var iframeElement = document.getElementById("preview");
var ACTIVE=null;

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function (xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

function replaceIframeContent(newHTML) {
    iframeElement.src = "about:blank";
    iframeElement.contentWindow.document.open();
    iframeElement.contentWindow.document.write(newHTML);
    iframeElement.contentWindow.document.close();
}

function send() {
    var content = "";
    var context = $context.val();
    if (ACTIVE === "#tab_html"){
        content = tinymce.activeEditor.getContent("id_html_content");
    }else if (ACTIVE === "#tab_subject"){
        content = $subject.val()
    }else if (ACTIVE === "#tab_content"){
        content = $content.val()
    }else{
        return
    }
    django.jQuery.post(render_url, {
            "content": content,
            "context": context
        },
        function (data) {
            replaceIframeContent(data)
        }
    );
}
function gotoParent(){
    var s1 = window.location.href;
    // nn = s1.replace(s1.split('/').pop(),'..');
    nn = s1.split("/").slice(0,-2).join("/")
    console.log(11111, nn);
    return nn + "/change/";
}

$context.on("change", function () {
    send()
})
$content.on("keyup", function () {
    send()
})
$(".button").on("click", function(e){
    $(".tab").hide();
    ACTIVE = $(this).data("panel");
    $(ACTIVE).show();
    send();
})
function setupTinyMCE(ed) {
    var typingTimer;                //timer identifier
    var doneTypingInterval = 500;  //time in ms, 5 seconds for example
    ed.on("keydown", function () {
        clearTimeout(typingTimer);
    })
    ed.on("change", function () {
        send();
    })
    ed.on("keyup", function () {
        clearTimeout(typingTimer);
        typingTimer = setTimeout(send, doneTypingInterval);
    })
}

$("#btn_content").click();
