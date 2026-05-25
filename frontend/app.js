let allJobs = [];

fetch("../jobs.json")
  .then(res => res.json())
  .then(data => {
    allJobs = data.jobs;
    renderJobs(allJobs);
  });

function renderJobs(jobs) {
  let container = document.getElementById("jobs");
  container.innerHTML = "";

  jobs.forEach(job => {
    container.innerHTML += `
      <div class="job-card">
        <h3>${job.title}</h3>
        <p><b>${job.company}</b></p>
        <p>Score: ${job.score}</p>
        <a class="apply" href="${job.link}" target="_blank">Apply Now</a>
      </div>
    `;
  });
}

function filterJobs(type) {
  if (type === "all") return renderJobs(allJobs);

  let filtered = allJobs.filter(j =>
    j.title.toLowerCase().includes(type) ||
    j.source?.toLowerCase().includes(type)
  );

  renderJobs(filtered);
}
