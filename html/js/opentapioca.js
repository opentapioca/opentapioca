

function constructAnnotatedOutput(response, addCheckboxes) {
	var curPos = 0;
	var curAnnotation = 0;
	var annotations = response.annotations;
	var html = $('<div></div>');
	var origText = response.text;
	while (curAnnotation < annotations.length) {
		var annotation = annotations[curAnnotation];
		var start = annotation.start;
		var end = annotation.end;
		var mention = origText.substr(start,end-start);
		html.append(origText.substr(curPos, start-curPos).replace(/\n/g,'<br/>'));
		var markup = $('<span class="bo" data-annotation-id="'+curAnnotation+'"><span class="bi"><span class="bw">'+mention+'</span></span></span>');
                markup.append(makePopupDiv(annotation, addCheckboxes));
                html.append(markup);
		curPos = end;
                curAnnotation++;
	}
	html.append(origText.substr(curPos, origText.length).replace(/\n/g, '<br/>'));
	return html;
}

function makePopupDiv(annotation, addCheckboxes) {
        var div = $('<div></div>').attr('class', 'annotation-popup');
        var ll = annotation.log_likelihood;
        var start = annotation.start;
        var end = annotation.end;
        var predicted_qid = annotation.best_qid;
        for(var i = 0; i < annotation.tags.length; i++) {
             var tag = annotation.tags[i];
             var label = tag.label ? tag.label[0]+' ('+tag.id+')' : tag.id;
             var description = tag.desc ? tag.desc : '';
             var rank = tag.rank;
             var statements = tag.nb_statements;
             var sitelinks = tag.nb_sitelinks;
             var score = tag.score;
             var tagDiv = $('<div></div>').attr('class', 'annotation-tag');
             if (predicted_qid == tag.id) {
                 tagDiv.addClass('predicted_valid');
             }
             $('<a></a>')
                .attr('href', 'https://www.wikidata.org/wiki/'+tag.id)
                .attr('target', '_blank')
                .text(label)
                .appendTo(tagDiv);
             var labelElem = $('<label></label>').appendTo(tagDiv);
             if(addCheckboxes) {
                 $('<input></input>')
                     .attr('type','checkbox')
                     .data('start', start)
                     .data('end', end)
                     .data('qid', tag.id)
                     .appendTo(labelElem);
             }
             $('<br /><span>'+description+'</span>').appendTo(labelElem);
             $('<br /><span class="scores">Rank: '+rank.toFixed(2)+', phrase: '+ll.toFixed(2)+'</span>').appendTo(labelElem);
             $('<br /><span class="scores">Statements: '+statements+', sitelinks: '+sitelinks+'</span>').appendTo(labelElem);
             if (score) {
                 $('<br /><span class="scores">Score: '+score+'</span>').appendTo(labelElem);
             }
             div.append(tagDiv);
        }
        return div;
}
        
/**** Gold standard annotation *****/

function nextDoc() {
   $.get('/api/get_doc',
           function (response) {
               var annotatedText = constructAnnotatedOutput(response, true);
               $('#doi').text(response.doi).attr('href', 'https://doi.org/'+response.doi);
               $('#demo_output').html("").append(annotatedText);
               $('#disambig_input').val(response.text);
   });
}

function storeJudgments() {
    var judgments = Array();
    $('.annotation-tag input').each(function(idx) {
        var input = $(this);
        judgments.push({
            start:input.data('start'),
            end:input.data('end'),
            qid:input.data('qid'),
            valid:input.prop('checked'),
        });
    });

    var payload = Object({
       doi: $('#doi').text(),
       doc: $('#disambig_input').val(),
       judgments: JSON.stringify(judgments),
    });

    $.post('/api/store_judgments',
           payload,
           function (response) {
               nextDoc();
    });
}

$(function() {
	$('#demo_push').click(function () {
		var query = $('#disambig_input').val();
		$.post('/api/annotate',
		  { query: query },
	          function (response) {
                        var annotatedText = constructAnnotatedOutput(response, false);
			$('#demo_output').html("").append(annotatedText);
	        });
	});

});

