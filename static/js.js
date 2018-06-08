Dropzone.autoDiscover = false;

$(function() {
  let myDropzone = new Dropzone("#dropFile", {
      url: '/uploadfile'
  });
  myDropzone.on('sending', function () {
      $('.fa-upload').addClass('grey-text text-lighten-4');
      $('.progress').removeClass('hide');
      $('#helpText').addClass('hide');
      $('#uploadText').removeClass('hide');
  });
  myDropzone.on('uploadprogress', function (file, per) {
      $('#percentText').html(Math.round(per));
      $('#progressBar').css({"width": Math.round(per)+"%"});
  });
  myDropzone.on('success', function (file, res) {
      console.log(res);
      console.log(res.st);
      console.log(res.mess);
      if(res.status === 'ok'){
          $('#uploadText').addClass('hide');
          $('#processText').removeClass('hide');
          $('#progressBar').removeClass('determinate').addClass('indeterminate');

          $('#filename').val(res.mess);

          $.ajax({
            type: 'POST',
            url: '/processfile',
            data: $('#options').serialize(),
            success: function(res){
                console.log(res);
                if(res.status === 'ok'){
                    $('.fa-upload').removeClass('grey-text text-lighten-4').addClass('fa-check-circle').removeClass('fa-upload');
                    $('.progress').addClass('hide');
                    $('#processText').addClass('hide');
                    $('#doneText').removeClass('hide');

                    window.location = res.mess;
                } else if(res.status === 'err'){
                    $('#uploadText').addClass('hide');
                    $('#errText').removeClass('hide');
                    $('.progress').addClass('hide');

                    $('.fa-upload').removeClass('grey-text text-lighten-4').addClass('fa-exclamation-circle').removeClass('fa-upload');
                    $('#errMess').html(res.mess);
                }
            },
            error: function (err) {
                console.log(err)
            }  
        });
      } else if(res.status === 'err'){
          $('#uploadText').addClass('hide');
          $('#errText').removeClass('hide');
          $('.progress').addClass('hide');

          $('.fa-upload').removeClass('grey-text text-lighten-4').addClass('fa-exclamation-circle').removeClass('fa-upload');
          $('#errMess').html(res.mess);
      }
  });

});