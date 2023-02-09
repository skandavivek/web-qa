let previous_url = "";

function validate_url(url) {
  let value = url.trim();

  if (value.startsWith("http") && value.length > 10 && value.includes(".")) {
    return true;
  }

  return false;
}

document.getElementById("url").addEventListener("keyup", function (event) {
  if (validate_url(event.target.value)) {
    document.getElementById("crawl-btn").disabled = false;
  } else {
    document.getElementById("crawl-btn").disabled = true;
    document.getElementById("process-btn").disabled = true;
    document.getElementById("text-before-phrase").disabled = true;
  }

  if (previous_url === event.target.value) {
    document.getElementById("text-before-phrase").disabled = false;
  }
});

function crawl_url() {
  let url = document.getElementById("url").value;

  let value = url.trim();

  if (!validate_url(value)) {
    alert("Please enter a valid URL");
    return;
  }

  document.getElementById("crawl-btn").disabled = true;

  fetch("/crawl", {
    method: "post",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url: value,
    }),
  })
    .then((response) => response.json())
    .then((json) => {
      console.log("Response text: ", json);

      if (json.status) {
        document.getElementById("process-btn").disabled = false;
        document.getElementById("text-before-phrase").disabled = false;
        previous_url = value;
      } else {
        console.error(json.error);
      }
      alert(json.message);
    })
    .finally(() => {
      document.getElementById("crawl-btn").disabled = false;
    });

  return;
}

document
  .getElementById("text-before-phrase")
  .addEventListener("keyup", function (event) {
    if (event.target.value.length > 0) {
      document.getElementById("process-btn").disabled = false;
    } else {
      document.getElementById("process-btn").disabled = true;
    }
  });

function process_text() {
  let text = document.getElementById("text-before-phrase").value;
  let url = document.getElementById("url").value;

  let value = text.trim();

  if (value.length < 1) {
    alert("Please enter some text");
    return;
  }

  document.getElementById("process-btn").disabled = true;

  fetch("/question", {
    method: "post",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url: url,
      question: value,
    }),
  })
    .then((response) => response.json())
    .then((json) => {
      console.log("Response text: ", json);

      if (json.status) {
        document.getElementById("text-after-phrase").value = json.data.answer;
      } else {
        console.error(json.error);
        alert(json.message);
      }
    })
    .finally(() => {
      document.getElementById("process-btn").disabled = false;
    });

  return;
}
