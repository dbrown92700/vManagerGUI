document.getElementById("upload").addEventListener("change", upload, false);
document.getElementById("download").addEventListener("click", download, false);

function upload(e) {

    var data = null;
    var file = e.target.files[0];

    var reader = new FileReader();
    reader.readAsText(file);
    reader.onload = function (event) {
        var csvData = event.target.result;

        var parsedCSV = d3.csv.parseRows(csvData);

        parsedCSV.forEach(function (d, i) {
            if (i == 0) return true; // skip the header
            // Set all 3 values for each row
            document.getElementsByName(d[0] + "0")[0].value = d[1];
            document.getElementsByName(d[0] + "1")[0].value = d[2];
            document.getElementsByName(d[0] + "2")[0].value = d[3];
        });
        // Pause 5 seconds and clear the filename to allow re-upload of the same file
        setTimeout(() => { document.getElementById("upload").value = ""; }, 5000);
    }
}

function download(e) {

    data = [];
    var f = d3.select("#formTable").selectAll("input")[0];

    f.forEach(function(d){
        data.push([d.name, d.value]);
    });

    var csvContent = "data:text/csv;charset=utf-8,Property,Description,Type,Category\n";

    var elementCount = (data.length - 1) / 3;

    for (let step = 0; step < elementCount; step++) {
        itemName = data[step * 3][0].replace(/.$/,'');
        csvContent += itemName + "," + data[step * 3][1] + "," + data[step * 3 + 1][1] + "," + data[step * 3 + 2][1] + "\n"
    };

    var encodedUri = encodeURI(csvContent);
    var link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "FormData.csv");
    link.click();
}
